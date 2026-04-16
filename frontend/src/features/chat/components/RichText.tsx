import { ReactNode } from "react";

type RichTextProps = {
  text: string;
};

type ListBlock = {
  type: "list";
  ordered: boolean;
  items: string[];
};

type ParagraphBlock = {
  type: "paragraph";
  text: string;
};

type Block = ListBlock | ParagraphBlock;

const ORDERED_LIST_RE = /^\s*\d+\.\s+(.*)$/;
const UNORDERED_LIST_RE = /^\s*[-*]\s+(.*)$/;
const INLINE_LINK_RE = /\[(.+?)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s]+)/g;

function trimTrailingPunctuation(url: string) {
  return url.replace(/[),.;:!?]+$/g, "");
}

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let matchIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = INLINE_LINK_RE.exec(text)) !== null) {
    const [raw] = match;
    const start = match.index;
    const end = start + raw.length;

    if (start > lastIndex) {
      nodes.push(text.slice(lastIndex, start));
    }

    if (match[1] && match[2]) {
      nodes.push(
        <a
          key={`${keyPrefix}-md-link-${matchIndex}`}
          href={match[2]}
          target="_blank"
          rel="noreferrer"
          className="underline underline-offset-2 break-all"
        >
          {match[1]}
        </a>
      );
    } else if (match[3]) {
      const cleanUrl = trimTrailingPunctuation(match[3]);
      const trailing = match[3].slice(cleanUrl.length);
      nodes.push(
        <a
          key={`${keyPrefix}-url-${matchIndex}`}
          href={cleanUrl}
          target="_blank"
          rel="noreferrer"
          className="underline underline-offset-2 break-all"
        >
          {cleanUrl}
        </a>
      );
      if (trailing) {
        nodes.push(trailing);
      }
    }

    lastIndex = end;
    matchIndex += 1;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}

function parseBlocks(text: string): Block[] {
  const lines = text.split(/\r?\n/);
  const blocks: Block[] = [];
  let paragraphLines: string[] = [];
  let listBlock: ListBlock | null = null;

  const flushParagraph = () => {
    if (paragraphLines.length === 0) return;
    blocks.push({
      type: "paragraph",
      text: paragraphLines.join("\n"),
    });
    paragraphLines = [];
  };

  const flushList = () => {
    if (!listBlock || listBlock.items.length === 0) return;
    blocks.push(listBlock);
    listBlock = null;
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const orderedMatch = line.match(ORDERED_LIST_RE);
    if (orderedMatch) {
      flushParagraph();
      if (!listBlock || !listBlock.ordered) {
        flushList();
        listBlock = {
          type: "list",
          ordered: true,
          items: [],
        };
      }
      listBlock.items.push(orderedMatch[1]);
      continue;
    }

    const unorderedMatch = line.match(UNORDERED_LIST_RE);
    if (unorderedMatch) {
      flushParagraph();
      if (!listBlock || listBlock.ordered) {
        flushList();
        listBlock = {
          type: "list",
          ordered: false,
          items: [],
        };
      }
      listBlock.items.push(unorderedMatch[1]);
      continue;
    }

    flushList();
    paragraphLines.push(line);
  }

  flushParagraph();
  flushList();

  return blocks;
}

export function RichText({ text }: RichTextProps) {
  const blocks = parseBlocks(text);

  return (
    <div className="space-y-2 break-words">
      {blocks.map((block, blockIndex) => {
        if (block.type === "paragraph") {
          return (
            <p key={`paragraph-${blockIndex}`} className="whitespace-pre-wrap">
              {renderInline(block.text, `paragraph-${blockIndex}`)}
            </p>
          );
        }

        if (block.ordered) {
          return (
            <ol key={`ordered-${blockIndex}`} className="list-decimal space-y-1 pl-5">
              {block.items.map((item, itemIndex) => (
                <li key={`ordered-${blockIndex}-${itemIndex}`}>{renderInline(item, `ordered-${blockIndex}-${itemIndex}`)}</li>
              ))}
            </ol>
          );
        }

        return (
          <ul key={`unordered-${blockIndex}`} className="list-disc space-y-1 pl-5">
            {block.items.map((item, itemIndex) => (
              <li key={`unordered-${blockIndex}-${itemIndex}`}>{renderInline(item, `unordered-${blockIndex}-${itemIndex}`)}</li>
            ))}
          </ul>
        );
      })}
    </div>
  );
}
