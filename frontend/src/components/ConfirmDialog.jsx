function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  isConfirming = false,
  onConfirm,
  onCancel,
}) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 px-4">
      <div
        className="w-full max-w-md rounded bg-white p-6 shadow"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <h2 id="confirm-dialog-title" className="text-lg font-semibold text-neutral-900">
          {title}
        </h2>
        <p className="mt-3 text-neutral-700">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded border border-neutral-300 px-3 py-2 text-neutral-900"
            type="button"
            onClick={onCancel}
            disabled={isConfirming}
          >
            {cancelLabel}
          </button>
          <button
            className="rounded bg-red-700 px-3 py-2 text-white disabled:opacity-60"
            type="button"
            onClick={onConfirm}
            disabled={isConfirming}
          >
            {isConfirming ? 'Deleting…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog
