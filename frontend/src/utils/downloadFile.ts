export async function downloadFileFromUrl(url: string, filename: string): Promise<void> {
  const response = await fetch(url, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error(`Échec du téléchargement (${response.status})`);
  }

  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);

  try {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } finally {
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  }
}

export async function createBlobUrlFromUrl(url: string): Promise<string> {
  const response = await fetch(url, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Échec du chargement (${response.status})`);
  }
  const blob = await response.blob();
  return window.URL.createObjectURL(blob);
} 