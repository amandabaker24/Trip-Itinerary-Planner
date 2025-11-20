import api from '../api/client'
import Button from './ui/Button'

type Props = {
  tripId: number
}

export default function PdfExportButton({ tripId }: Props) {
  const handleDownload = async () => {
    const response = await api.get(`/trips/${tripId}/export/pdf`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `trip-${tripId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  return <Button onClick={handleDownload}>Export PDF</Button>
}
