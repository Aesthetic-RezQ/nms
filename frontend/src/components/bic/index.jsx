import React, { createContext, useContext, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';

const classes = (...values) => values.filter(Boolean).join(' ');
const FieldContext = createContext({});
const DialogContext = createContext({});

// Thin semantic React bindings for the shared BIC CSS framework.
const element = (tag, base) => function Component({ as: Tag = tag, className, ...props }) {
  return <Tag className={classes(base, className)} {...props} />;
};

export const Card = element('div', 'bic-card');
Card.Header = element('div', 'bic-card-header');
Card.Body = element('div', 'bic-card-body');
Card.Footer = element('div', 'bic-card-footer');

export const Row = element('div', 'bic-row');
export function Col({ xs, sm, md, lg, className, ...props }) {
  return <div className={classes('bic-col', ...Object.entries({ xs, sm, md, lg })
    .filter(([, span]) => span != null).map(([breakpoint, span]) => `bic-col-${breakpoint}-${span}`), className)} {...props} />;
}

export function Button({ variant = 'primary', size, className, type = 'button', title, ...props }) {
  const tone = ['primary', 'secondary', 'danger'].includes(variant) ? variant : 'secondary';
  return <button type={type} title={title} aria-label={props['aria-label'] || title}
    className={classes('bic-btn', `bic-btn-${tone}`, size === 'sm' && 'bic-btn-sm', className)} {...props} />;
}
export function ButtonGroup({ size, className, ...props }) {
  return <div role="group" className={classes('bic-button-group', size === 'sm' && 'bic-button-group-sm', className)} {...props} />;
}

const unsortableColumnLabels = new Set(['action', 'actions', 'change', 'changes']);

const normalizeSortValue = (value) => {
  const text = String(value || '').trim();
  if (!text || ['—', 'n/a', 'pending', 'ongoing', 'uncorrelated'].includes(text.toLowerCase())) return null;

  const ipAddress = text.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (ipAddress) return { type: 'number', value: ipAddress.slice(1).reduce((total, part) => total * 256 + Number(part), 0) };

  const duration = text.match(/^(-?\d+(?:\.\d+)?)\s*(ms|s|m|h|d|%)?$/i);
  if (duration) {
    const multipliers = { ms: 1, s: 1000, m: 60000, h: 3600000, d: 86400000, '%': 1 };
    return { type: 'number', value: Number(duration[1]) * (multipliers[(duration[2] || '').toLowerCase()] || 1) };
  }

  const date = Date.parse(text);
  if (!Number.isNaN(date) && /\d/.test(text)) return { type: 'number', value: date };
  return { type: 'text', value: text };
};

const compareRows = (left, right, columnIndex, direction) => {
  const leftValue = normalizeSortValue(left.cells[columnIndex]?.dataset.sortValue || left.cells[columnIndex]?.textContent);
  const rightValue = normalizeSortValue(right.cells[columnIndex]?.dataset.sortValue || right.cells[columnIndex]?.textContent);
  if (!leftValue && !rightValue) return 0;
  if (!leftValue) return 1;
  if (!rightValue) return -1;

  const result = leftValue.type === 'number' && rightValue.type === 'number'
    ? leftValue.value - rightValue.value
    : String(leftValue.value).localeCompare(String(rightValue.value), undefined, { numeric: true, sensitivity: 'base' });
  return direction === 'asc' ? result : -result;
};

export function Table({ responsive, hover, sortable = true, className, children, ...props }) {
  const tableRef = useRef(null);
  const [sort, setSort] = useState(null);

  useLayoutEffect(() => {
    const table = tableRef.current;
    if (!table) return;
    const headers = [...table.querySelectorAll('thead th')];
    headers.forEach((header, columnIndex) => {
      const label = header.textContent.trim().toLowerCase();
      const canSort = sortable && header.dataset.sortable !== 'false' && !unsortableColumnLabels.has(label);
      header.classList.toggle('bic-sortable-header', canSort);
      header.classList.toggle('is-sort-asc', canSort && sort?.columnIndex === columnIndex && sort.direction === 'asc');
      header.classList.toggle('is-sort-desc', canSort && sort?.columnIndex === columnIndex && sort.direction === 'desc');
      if (!canSort) {
        header.removeAttribute('tabindex');
        header.removeAttribute('aria-sort');
        return;
      }
      header.tabIndex = 0;
      header.setAttribute('aria-sort', sort?.columnIndex === columnIndex ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none');
    });
  }, [children, sortable, sort]);

  useLayoutEffect(() => {
    if (!sort) return;
    const table = tableRef.current;
    if (!table) return;
    [...table.tBodies].forEach(body => {
      const rows = [...body.rows].filter(row => row.cells.length > sort.columnIndex && [...row.cells].every(cell => cell.colSpan === 1));
      rows.sort((left, right) => compareRows(left, right, sort.columnIndex, sort.direction));
      rows.forEach(row => body.appendChild(row));
    });
  }, [children, sort]);

  const requestSort = (header) => {
    const headers = [...tableRef.current?.querySelectorAll('thead th') || []];
    const columnIndex = headers.indexOf(header);
    if (columnIndex < 0 || !header.classList.contains('bic-sortable-header')) return;
    setSort(current => ({
      columnIndex,
      direction: current?.columnIndex === columnIndex && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const onHeaderClick = event => requestSort(event.target.closest('th'));
  const onHeaderKeyDown = event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const header = event.target.closest('th');
    if (!header?.classList.contains('bic-sortable-header')) return;
    event.preventDefault();
    requestSort(header);
  };

  return <div className="bic-table-wrap" tabIndex={0} role="region" aria-label={props['aria-label'] || 'Data table'}>
    <table ref={tableRef} className={classes('bic-table', className)} onClick={onHeaderClick} onKeyDown={onHeaderKeyDown} {...props}>{children}</table>
  </div>;
}

export function Badge({ bg = 'info', className, children, ...props }) {
  const tone = ['success', 'warning', 'danger', 'info'].includes(bg) ? bg : 'info';
  return <span className={classes('bic-badge', `bic-badge-${tone}`, className)} {...props}>{children}</span>;
}
export function Alert({ variant = 'info', className, ...props }) {
  return <div role={variant === 'danger' ? 'alert' : 'status'} className={classes('bic-alert', `bic-alert-${variant}`, className)} {...props} />;
}
Alert.Heading = element('h2', 'bic-section-title');

export function Spinner({ size, className, label = 'Loading', ...props }) {
  return <span role="status" className={classes('bic-loading', className)} {...props}>
    <span aria-hidden="true" className={classes('bic-spinner', size === 'sm' && 'bic-spinner-sm')} />
    <span className="bic-sr-only">{label}</span>
  </span>;
}

export const Form = element('form');
Form.Group = function FormGroup({ controlId, className, children, ...props }) {
  const generatedId = useId();
  const id = controlId || generatedId;
  const fields = React.Children.toArray(children);
  const hasHelp = fields.some(child => child.type === Form.Text);
  const hasFeedback = fields.some(child => child.type === Form.Control.Feedback && child.props.children);
  return <FieldContext.Provider value={{ id, helpId: hasHelp ? `${id}-help` : undefined, feedbackId: hasFeedback ? `${id}-feedback` : undefined }}>
    <div className={classes('bic-form-group', className)} {...props}>{children}</div>
  </FieldContext.Provider>;
};
Form.Label = function FormLabel({ className, htmlFor, ...props }) {
  const { id } = useContext(FieldContext);
  return <label className={classes('bic-label', className)} htmlFor={htmlFor || id} {...props} />;
};
function Control({ as: Tag = 'input', className, isInvalid, id, ...props }) {
  const field = useContext(FieldContext);
  return <Tag id={id || field.id} aria-invalid={isInvalid || undefined}
    aria-describedby={classes(field.helpId, field.feedbackId) || undefined}
    className={classes(Tag === 'textarea' ? 'bic-textarea' : Tag === 'select' ? 'bic-select' : 'bic-control', isInvalid && 'is-invalid', className)} {...props} />;
}
Form.Control = Control;
Form.Select = function Select(props) { return <Control as="select" {...props} />; };
Form.Text = function Help({ className, ...props }) {
  const { helpId } = useContext(FieldContext);
  return <div id={helpId} className={classes('bic-help', className)} {...props} />;
};
Form.Control.Feedback = function Feedback({ type, children, ...props }) {
  const { feedbackId } = useContext(FieldContext);
  return children ? <div id={feedbackId} className="bic-feedback" role="alert" {...props}>{children}</div> : null;
};
Form.Check = function Check({ type = 'checkbox', id, label, className, ...props }) {
  const generatedId = useId();
  const inputId = id || generatedId;
  return <div className={classes('bic-check', className)}>
    <input id={inputId} type={type === 'switch' ? 'checkbox' : type} role={type === 'switch' ? 'switch' : undefined}
      className="bic-check-input" {...props} />
    {label && <label htmlFor={inputId}>{label}</label>}
  </div>;
};

export function Modal({ show, onHide, size, centered, children }) {
  const ref = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!show) return;
    const previousFocus = document.activeElement;
    dialog.showModal();
    return () => {
      dialog.close();
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, [show]);
  return <DialogContext.Provider value={{ onHide, titleId }}>
    <dialog ref={ref} className={classes('bic-modal', size === 'lg' && 'bic-modal-lg')} aria-labelledby={titleId}
      onCancel={event => { event.preventDefault(); onHide?.(); }}
      onClick={event => {
        if (event.target !== event.currentTarget) return;
        const bounds = event.currentTarget.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onHide?.();
      }}>
      {show && children}
    </dialog>
  </DialogContext.Provider>;
}
Modal.Header = function ModalHeader({ closeButton, className, children, ...props }) {
  const { onHide } = useContext(DialogContext);
  return <div className={classes('bic-modal-header', className)} {...props}>
    {children}
    {closeButton && <Button variant="secondary" size="sm" onClick={onHide} aria-label="Close dialog">Close</Button>}
  </div>;
};
Modal.Title = function ModalTitle({ className, ...props }) {
  const { titleId } = useContext(DialogContext);
  return <h2 id={titleId} className={classes('bic-section-title', 'bic-mb-0', className)} {...props} />;
};
Modal.Body = element('div', 'bic-modal-body');
Modal.Footer = element('div', 'bic-modal-footer');

export function Pagination({ className, children }) {
  return <nav aria-label="Pagination" className={classes('bic-pagination', className)}>{children}</nav>;
}
Pagination.Item = function PageItem({ active, ...props }) {
  return <Button variant={active ? 'primary' : 'secondary'} size="sm" aria-current={active ? 'page' : undefined} {...props} />;
};
Pagination.Prev = props => <Button variant="secondary" size="sm" aria-label="Previous page" {...props}>Previous</Button>;
Pagination.Next = props => <Button variant="secondary" size="sm" aria-label="Next page" {...props}>Next</Button>;

export function Stat({ label, value, meta, tone, icon: Icon, className }) {
  return (
    <div className={classes('bic-card', 'bic-stat', tone && `bic-stat-${tone}`, className)}>
      <div className="bic-stat-inner">
        <div className="bic-stat-content">
          <div className="bic-stat-label">{label}</div>
          <div className={classes('bic-stat-value', tone && `bic-text-${tone}`)}>{value}</div>
          {meta && <div className="bic-stat-meta">{meta}</div>}
        </div>
        {Icon && (
          <div className={classes('bic-stat-avatar', tone && `bic-stat-avatar-${tone}`)}>
            <Icon />
          </div>
        )}
      </div>
    </div>
  );
}

