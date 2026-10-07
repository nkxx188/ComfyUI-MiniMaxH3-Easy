const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const source = fs.readFileSync(
    path.join(__dirname, "../web/minimax_h3_easy_ui.js"),
    "utf8",
);
const functionNames = [
    "mediaLoaderState", "mediaLoaderEntryUrl", "mediaLoaderMentionOptions",
    "truncateMentionLabel", "findMentionOption", "refreshMentionPreviews",
    "updateMentionChip", "makeAudioIcon", "makeMentionThumb", "makeMentionChip",
    "promptMentionTag", "promptTextFromPart", "promptDocTextFromParts",
    "pastedMentionCandidates", "pastedOfficialMediaTagMatch", "promptPartsFromText",
    "serializeEditorDoc", "renderEditorFromNode", "syncPromptFromEditor",
    "mediaLoaderWriteState",
];
const functionSource = functionNames.map((name) => {
    const match = source.match(new RegExp(`^function ${name}\\([^]*?^}`, "m"));
    assert.ok(match, `Missing production function: ${name}`);
    return match[0];
}).join("\n");
const docKey = source.match(/const PROMPT_DOC_PROP = "([^"]+)"/)[1];

// Minimal DOM surface for exercising the real chip/thumbnail render code.
class Element {
    constructor(tag = "span") {
        this.nodeType = 1;
        this.tagName = tag.toUpperCase();
        this.dataset = {};
        this.childNodes = [];
        this.className = "";
        this.style = {};
        this.classList = {
            contains: (name) => this.className.split(/\s+/).includes(name),
            toggle: (name, enabled) => {
                const names = new Set(this.className.split(/\s+/).filter(Boolean));
                if (enabled) names.add(name);
                else names.delete(name);
                this.className = [...names].join(" ");
            },
        };
    }
    append(...children) {
        for (const child of children) {
            child.parentElement = this;
            this.childNodes.push(child);
        }
    }
    prepend(child) {
        child.parentElement = this;
        this.childNodes.unshift(child);
    }
    replaceWith(child) {
        const parent = this.parentElement;
        child.parentElement = parent;
        parent.childNodes[parent.childNodes.indexOf(this)] = child;
    }
    querySelectorAll(selector) {
        const found = [];
        for (const child of this.childNodes) {
            if (child.classList?.contains(selector.slice(1))) found.push(child);
            if (child.querySelectorAll) found.push(...child.querySelectorAll(selector));
        }
        return found;
    }
    querySelector(selector) {
        return this.querySelectorAll(selector)[0] || null;
    }
    set textContent(text) {
        this.childNodes = text ? [{ nodeType: 3, textContent: text }] : [];
    }
    get textContent() {
        return this.childNodes.map((child) => child.textContent || "").join("");
    }
    setAttribute() {}
    addEventListener() {}
}

function fixture(state = { images: ["left.png", "right.png"] }, mode = "filename") {
    const noop = () => {};
    const loader = {
        id: 100,
        isLoader: true,
        properties: {},
        widgets: [{ name: "media_state", value: JSON.stringify(state) }],
        setDirtyCanvas: noop,
    };
    const node = {
        id: 200,
        mode,
        properties: {},
        widgets: [{ name: "prompt", value: "" }],
        setDirtyCanvas: noop,
    };
    const editor = new Element("div");
    node.__h3Editor = editor;
    let refreshPending = false;
    const context = vm.createContext({
        Node: { TEXT_NODE: 3, ELEMENT_NODE: 1 },
        document: { activeElement: null, createElement: (tag) => new Element(tag) },
        URLSearchParams,
        PROMPT_DOC_PROP: docKey,
        AUDIO_ICON_SVG: "audio-icon",
        ZH_BROWSER: false,
        LABELS: { image: "Image", audio: "Audio", video: "Video" },
        TEXT: { mediaLoaderMenuTitle: "Media Loader" },
        MEDIA_LOADER_GROUPS: [
            { key: "images" }, { key: "audios" }, { key: "videos" },
        ],
        app: { graph: { _nodes: [loader, node], setDirtyCanvas: noop, change: noop } },
        isMediaLoader: (candidate) => Boolean(candidate?.isLoader),
        isTarget: (candidate) => candidate === node,
        canUseMediaMentions: () => true,
        normalizeLinks: noop,
        referenceMentionMode: (candidate) => candidate.mode,
        getWidget: (candidate, name) => candidate.widgets.find((w) => w.name === name),
        getWidgetValue: (candidate, name, fallback) =>
            candidate.widgets.find((w) => w.name === name)?.value ?? fallback,
        isRawPromptMode: () => false,
        editorPromptNode: () => node,
        isDialogueBlock: () => false,
        closeMentionMenu: noop,
        syncModeWidgets: noop,
        syncSegmentSummary: noop,
        appendTextWithBreaks: (container, text) => {
            if (text) container.append({ nodeType: 3, textContent: text });
        },
        requestMentionPreviewRefresh: () => { refreshPending = true; },
    });
    vm.runInContext(functionSource, context);
    context.mentionOptions = () => context.mediaLoaderMentionOptions(loader, node);
    const flush = () => {
        if (refreshPending) {
            refreshPending = false;
            context.refreshMentionPreviews();
        }
    };
    const insert = (type, ordinal) => {
        const option = context.mentionOptions().find((item) =>
            item.type === type && item.ordinal === ordinal);
        assert.ok(option);
        editor.append(context.makeMentionChip(option));
        context.syncPromptFromEditor(node, false);
    };
    return { context, loader, node, editor, flush, insert };
}

function mentions(editor) {
    return editor.querySelectorAll(".h3-mention-chip");
}

function checkChip(chip, filename, tag, label = `@${filename.split("/").pop()}`) {
    assert.equal(chip.dataset.filename, filename);
    assert.equal(chip.dataset.tag, tag);
    assert.equal(chip.querySelector(".h3-mention-chip-label").textContent, label);
    if (chip.dataset.mediaType !== "audio") {
        const thumbnail = chip.querySelector(".h3-mention-chip-thumb");
        assert.equal(new URL(thumbnail.src, "http://localhost").searchParams.get("filename"), filename);
    }
}

test("filename mode swaps labels and thumbnails while keeping each H3 position", () => {
    const f = fixture();
    f.insert("image", 1);
    f.insert("image", 2);
    f.context.mediaLoaderWriteState(f.loader, { images: ["right.png", "left.png"] });
    f.flush();
    const chips = mentions(f.editor);
    checkChip(chips[0], "right.png", "<Picture 1>");
    checkChip(chips[1], "left.png", "<Picture 2>");
    assert.equal(f.node.widgets[0].value, "<Picture 1><Picture 2>");
    assert.equal(f.node.properties[docKey].parts[0].filename, "right.png");
    assert.equal(f.node.properties[docKey].parts[1].filename, "left.png");

    f.node.properties = JSON.parse(JSON.stringify(f.node.properties));
    f.context.renderEditorFromNode(f.node, true);
    checkChip(mentions(f.editor)[0], "right.png", "<Picture 1>");
    checkChip(mentions(f.editor)[1], "left.png", "<Picture 2>");
});

test("optimizer output with multiple and repeated references stays distinct", () => {
    const f = fixture({ images: ["one.png", "two.png", "three.png", "four.png"] });
    const text = "<Picture 1> turns; <Picture 2> waves; <Picture 3> speaks; <Picture 4> waits; <Picture 2> sits.";
    f.node.properties[docKey] = {
        version: 1,
        text,
        parts: f.context.promptPartsFromText(f.node, text),
    };
    f.context.renderEditorFromNode(f.node, true);
    f.context.refreshMentionPreviews();
    const expected = ["one.png", "two.png", "three.png", "four.png", "two.png"];
    mentions(f.editor).forEach((chip, index) => {
        checkChip(chip, expected[index], `<Picture ${[1, 2, 3, 4, 2][index]}>`);
    });
    assert.equal(f.node.widgets[0].value, text);

    f.context.mediaLoaderWriteState(f.loader, {
        images: ["four.png", "three.png", "two.png", "one.png"],
    });
    f.flush();
    const after = ["four.png", "three.png", "two.png", "one.png", "three.png"];
    mentions(f.editor).forEach((chip, index) => {
        checkChip(chip, after[index], `<Picture ${[1, 2, 3, 4, 2][index]}>`);
    });
    assert.equal(f.node.widgets[0].value, text);
});

test("switching index to filename preserves distinct references before and after swapping", () => {
    const f = fixture(undefined, "index");
    f.insert("image", 1);
    f.insert("image", 2);
    f.node.mode = "filename";
    f.context.refreshMentionPreviews();
    checkChip(mentions(f.editor)[0], "left.png", "<Picture 1>");
    checkChip(mentions(f.editor)[1], "right.png", "<Picture 2>");

    f.context.mediaLoaderWriteState(f.loader, { images: ["right.png", "left.png"] });
    f.flush();
    f.node.mode = "index";
    f.context.refreshMentionPreviews();
    checkChip(mentions(f.editor)[0], "right.png", "<Picture 1>", "@Image1");
    checkChip(mentions(f.editor)[1], "left.png", "<Picture 2>", "@Image2");
    f.node.mode = "filename";
    f.context.refreshMentionPreviews();
    checkChip(mentions(f.editor)[0], "right.png", "<Picture 1>");
    checkChip(mentions(f.editor)[1], "left.png", "<Picture 2>");
});

test("image, video and audio positions stay independent", () => {
    const f = fixture({
        images: ["image1.png", "image2.png"],
        videos: ["video1.mp4", "video2.mp4"],
        audios: ["audio1.wav", "audio2.wav"],
    });
    for (const type of ["image", "video", "audio"]) {
        f.insert(type, 1);
        f.insert(type, 2);
    }
    f.context.mediaLoaderWriteState(f.loader, {
        images: ["image2.png", "image1.png"],
        videos: ["video1.mp4", "video2.mp4"],
        audios: ["audio2.wav", "audio1.wav"],
    });
    f.flush();
    const chips = mentions(f.editor);
    checkChip(chips[0], "image2.png", "<Picture 1>");
    checkChip(chips[1], "image1.png", "<Picture 2>");
    checkChip(chips[2], "video1.mp4", "<Video 1>");
    checkChip(chips[3], "video2.mp4", "<Video 2>");
    checkChip(chips[4], "audio2.wav", "<Audio 1>");
    checkChip(chips[5], "audio1.wav", "<Audio 2>");
});

test("equal basenames in different folders do not collapse references", () => {
    const f = fixture({ images: ["a/person.png", "b/person.png"] });
    f.insert("image", 1);
    f.insert("image", 2);
    f.context.mediaLoaderWriteState(f.loader, { images: ["b/person.png", "a/person.png"] });
    f.flush();
    checkChip(mentions(f.editor)[0], "b/person.png", "<Picture 1>");
    checkChip(mentions(f.editor)[1], "a/person.png", "<Picture 2>");
});

test("a missing media-loader position is unresolved instead of matched to another slot", () => {
    const f = fixture();
    f.insert("image", 2);
    f.context.mediaLoaderWriteState(f.loader, { images: ["right.png"] });
    f.flush();
    const chip = mentions(f.editor)[0];
    assert.equal(chip.dataset.tag, "<Picture 2>");
    assert.ok(chip.classList.contains("is-unresolved"));
    assert.equal(chip.dataset.previewUrl, "");
});

test("single-file node connections still bind by source rather than ordinal", () => {
    const f = fixture();
    const options = [
        { type: "image", sourceId: 9, sourceSlot: 0, ordinal: 1, fullLabel: "other.png" },
        { type: "image", sourceId: 8, sourceSlot: 0, ordinal: 2, fullLabel: "original.png" },
    ];
    const reference = { mediaType: "image", sourceId: 8, sourceSlot: 0, ordinal: 1 };
    assert.equal(f.context.findMentionOption(options, reference, "filename"), options[1]);
    assert.equal(f.context.findMentionOption(options, reference, "index"), options[0]);
});

test("legacy documents without filenames and unconnected tags resolve by position", () => {
    const f = fixture();
    const options = f.context.mentionOptions();
    assert.equal(f.context.findMentionOption(options, {
        mediaType: "image", sourceId: 100, sourceSlot: 0, ordinal: 2,
    }, "filename"), options[1]);
    assert.equal(f.context.findMentionOption(options, {
        mediaType: "image", sourceId: null, ordinal: 2,
    }, "filename"), options[1]);
});
