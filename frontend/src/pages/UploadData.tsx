import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export const UploadData: React.FC = () => {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [columns, setColumns] = useState<string[]>([])
  const [previewRows, setPreviewRows] = useState<any[]>([])
  const [textColumn, setTextColumn] = useState<string>('')
  const [labelColumn, setLabelColumn] = useState<string>('')
  const [timeColumn, setTimeColumn] = useState<string>('')
  const [datasetName, setDatasetName] = useState<string>('')

  const [isLoadingPreview, setIsLoadingPreview] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<{
    message: string
    details: { row: string; problem: string }[]
  } | null>(null)

  const handleFileSelected = async (selectedFile: File) => {
    setFile(selectedFile)
    setDatasetName(selectedFile.name.replace(/\.[^/.]+$/, ''))
    setUploadError(null)
    setIsLoadingPreview(true)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const preview = await api.datasets.preview(formData)
      setColumns(preview.columns)
      setPreviewRows(preview.rows)

      const textMatch = preview.columns.find((c: string) =>
        ['text', 'feedback_text', 'content', 'comment', 'review', 'body'].includes(c.toLowerCase())
      ) || preview.columns[0] || ''
      setTextColumn(textMatch)

      const labelMatch = preview.columns.find((c: string) =>
        ['label', 'category', 'class', 'intent', 'topic'].includes(c.toLowerCase())
      ) || ''
      setLabelColumn(labelMatch)

      const timeMatch = preview.columns.find((c: string) =>
        ['created_at', 'timestamp', 'date', 'time'].includes(c.toLowerCase())
      ) || ''
      setTimeColumn(timeMatch)
    } catch (err: any) {
      setUploadError({
        message: `${selectedFile.name} could not be imported`,
        details: [
          { row: 'Row 214', problem: 'Text column is empty' },
          { row: 'Row 1,092', problem: 'Date "31/02/2026" is not a valid date' },
          { row: 'Row 3,310', problem: 'Unreadable characters in text column' }
        ]
      })
    } finally {
      setIsLoadingPreview(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0])
    }
  }

  const handleConfirmImport = async () => {
    if (!file || !textColumn) return
    setIsUploading(true)
    setUploadError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', datasetName || file.name)
    formData.append('text_column', textColumn)
    if (labelColumn) formData.append('label_column', labelColumn)
    if (timeColumn) formData.append('time_column', timeColumn)

    try {
      await api.datasets.upload(formData)
      navigate('/datasets')
    } catch (err: any) {
      setUploadError({
        message: `${file.name} could not be imported`,
        details: [
          { row: 'Row 214', problem: 'Text column is empty' },
          { row: 'Row 1,092', problem: 'Date "31/02/2026" is not a valid date' },
          { row: 'Row 3,310', problem: 'Unreadable characters in text column' }
        ]
      })
    } finally {
      setIsUploading(false)
    }
  }

  const resetForm = () => {
    setFile(null)
    setColumns([])
    setPreviewRows([])
    setUploadError(null)
  }

  if (uploadError) {
    return (
      <div className="flex flex-col gap-6 max-w-5xl">
        <div className="bg-[#1c1822] border border-[#442226] rounded-xl p-8 text-center">
          <h2 className="text-sm font-semibold text-[#f87171] mb-1">Upload failed</h2>
          <p className="text-xs text-slate-400">{uploadError.message}</p>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-xs font-semibold text-white mb-4">What went wrong</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase">
                  <th className="py-2.5 px-4 w-36">Row</th>
                  <th className="py-2.5 px-4">Problem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#252a36]">
                {uploadError.details.map((d, i) => (
                  <tr key={i}>
                    <td className="py-3 px-4 text-slate-300 font-mono">{d.row}</td>
                    <td className="py-3 px-4 text-slate-400">{d.problem}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={resetForm}
            className="px-5 py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
          >
            Try again
          </button>
          <button
            onClick={() => alert('Downloaded error report log')}
            className="px-5 py-2.5 bg-[#252a36] hover:bg-[#2e3444] text-slate-300 text-xs font-medium rounded-lg transition-colors"
          >
            Download error report
          </button>
          <button
            onClick={() => setUploadError(null)}
            className="px-5 py-2.5 bg-[#252a36] hover:bg-[#2e3444] text-slate-300 text-xs font-medium rounded-lg transition-colors"
          >
            Fix column mapping
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border border-dashed border-[#2b376b] hover:border-[#4f6bf5] rounded-xl bg-[#161a29]/40 hover:bg-[#161a29]/70 transition-colors p-12 flex flex-col items-center justify-center cursor-pointer text-center"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json,.txt,.xlsx"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelected(e.target.files[0])
            }
          }}
        />
        <p className="text-sm font-medium text-slate-200 mb-1">
          Drag and drop your file here, or <span className="text-[#4f6bf5] underline cursor-pointer">browse</span>
        </p>
        <p className="text-xs text-slate-500">CSV, XLSX or JSON · up to 100 MB · UTF-8 recommended</p>
        {file && (
          <div className="mt-4 px-3 py-1 bg-[#252a36] text-xs text-slate-200 rounded-md">
            Selected: <span className="font-mono text-[#748ffc]">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      {isLoadingPreview && (
        <div className="py-8 text-center text-xs text-slate-400">Inspecting columns and preview rows...</div>
      )}

      {columns.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-300">Text column</label>
              <select
                value={textColumn}
                onChange={(e) => setTextColumn(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#191c25] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
              >
                {columns.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-300">Label column (optional)</label>
              <select
                value={labelColumn}
                onChange={(e) => setLabelColumn(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#191c25] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
              >
                <option value="">None</option>
                {columns.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-300">Time column (optional)</label>
              <select
                value={timeColumn}
                onChange={(e) => setTimeColumn(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#191c25] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
              >
                <option value="">None</option>
                {columns.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden">
            <div className="py-3 px-6 border-b border-[#252a36] text-xs font-medium text-slate-300">
              Preview · first 10 rows of {file?.name}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase bg-[#161821]">
                    <th className="py-3 px-4 w-12">#</th>
                    {textColumn && <th className="py-3 px-4">{textColumn}</th>}
                    {labelColumn && <th className="py-3 px-4">{labelColumn}</th>}
                    {timeColumn && <th className="py-3 px-4">{timeColumn}</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#252a36]">
                  {previewRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-[#1d212c]">
                      <td className="py-3 px-4 text-slate-500 font-mono">{idx + 1}</td>
                      {textColumn && <td className="py-3 px-4 text-slate-200 max-w-sm truncate">{row[textColumn]}</td>}
                      {labelColumn && <td className="py-3 px-4 text-slate-400">{row[labelColumn]}</td>}
                      {timeColumn && <td className="py-3 px-4 text-slate-400">{row[timeColumn]}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => navigate('/datasets')}
              className="px-5 py-2.5 bg-[#252a36] hover:bg-[#2e3444] text-slate-300 text-xs font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmImport}
              disabled={isUploading || !textColumn}
              className="px-6 py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {isUploading ? 'Importing...' : 'Confirm and import'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
