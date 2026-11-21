import { useEffect, useId, useRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { X, ArrowUpRight, AlertTriangle } from 'lucide-react';

export type Language = 'en' | 'ja';
export const word = (lang: Language, en: string, ja: string) => (lang === 'ja' ? ja : en);
export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'cyan' | 'green' | 'amber' | 'neutral' | 'red';
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
export function Panel({
  children,
  title,
  eyebrow,
  action,
  className = '',
}: {
  children: ReactNode;
  title?: ReactNode;
  eyebrow?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || eyebrow || action) && (
        <div className="panel-heading">
          <div>
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            {title && <h2>{title}</h2>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
export function Button({
  children,
  variant = 'secondary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
}) {
  return (
    <button type="button" className={`button button-${variant} ${className}`} {...props}>
      {children}
    </button>
  );
}
export function EmptyState({
  title,
  children,
  icon,
}: {
  title: string;
  children: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon || <ArrowUpRight size={22} />}</div>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Notice({
  children,
  tone = 'info',
}: {
  children: ReactNode;
  tone?: 'info' | 'warning' | 'error';
}) {
  return (
    <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <AlertTriangle size={16} />
      <span>{children}</span>
    </div>
  );
}
export function DemoNotice({ lang }: { lang: Language }) {
  return (
    <Notice>
      {word(
        lang,
        'Demo workspace · Sample data and in-memory interactions. No model, tools or system resources are connected.',
        'Demoワークスペース · サンプルデータとメモリ内の操作です。モデル・Tool・システム資源には接続していません。',
      )}
    </Notice>
  );
}
export function Modal({
  title,
  children,
  onClose,
  closeLabel = 'Close',
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  closeLabel?: string;
}) {
  const id = useId();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = ref.current;
    const previous = document.activeElement;
    node?.showModal();
    return () => {
      node?.close();
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby={id}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="modal-heading">
        <h2 id={id}>{title}</h2>
        <button className="icon-button" aria-label={closeLabel} onClick={onClose}>
          <X size={19} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
