import { Fragment, type ReactNode } from 'react';

// A deliberately small, text-only Markdown renderer. No HTML or executable URLs.
function inline(text: string): ReactNode[] {
  return text
    .split(/(`[^`]+`|\*\*[^*]+\*\*)/g)
    .map((part, i) =>
      part.startsWith('`') ? (
        <code key={i}>{part.slice(1, -1)}</code>
      ) : part.startsWith('**') ? (
        <strong key={i}>{part.slice(2, -2)}</strong>
      ) : (
        <Fragment key={i}>{part}</Fragment>
      ),
    );
}
export function Markdown({ text }: { text: string }) {
  return (
    <div className="markdown">
      {text.split(/(```[\s\S]*?(?:```|$))/g).map((part, index) => {
        if (part.startsWith('```')) {
          const firstLine = part.indexOf('\n');
          const code =
            firstLine < 0 ? part.slice(3) : part.slice(firstLine + 1).replace(/```$/, '');
          const language = firstLine < 0 ? '' : part.slice(3, firstLine).trim();
          return (
            <div className="code-block" key={index}>
              <div className="code-language">{language || 'code'}</div>
              <pre>
                <code>{code}</code>
              </pre>
            </div>
          );
        }
        return (
          <Fragment key={index}>
            {part
              .split(/\n\s*\n/)
              .filter(Boolean)
              .map((paragraph, j) => {
                if (/^#{1,3} /.test(paragraph))
                  return <h3 key={j}>{inline(paragraph.replace(/^#{1,3} /, ''))}</h3>;
                if (paragraph.split('\n').every((line) => /^[-*] /.test(line)))
                  return (
                    <ul key={j}>
                      {paragraph.split('\n').map((line, k) => (
                        <li key={k}>{inline(line.slice(2))}</li>
                      ))}
                    </ul>
                  );
                return <p key={j}>{inline(paragraph)}</p>;
              })}
          </Fragment>
        );
      })}
    </div>
  );
}
