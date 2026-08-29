import { memo, useState } from 'react'

import { type ImageData } from '@/types/os'
import { cn } from '@/lib/utils'

const ImageItem = ({ image }: { image: ImageData }) => {
  const [hasError, setHasError] = useState(false)

  if (hasError) {
    return (
      <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-md bg-secondary/50 p-2 text-muted">
        <p className="text-primary">Image unavailable</p>
        <a
          href={image.url}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full max-w-md truncate p-2 text-center text-xs text-primary underline"
        >
          {image.url}
        </a>
      </div>
    )
  }

  return (
    <div className="group relative">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={image.url}
        alt={image.revised_prompt || 'AI generated image'}
        className="w-full rounded-lg"
        onError={() => setHasError(true)}
      />
    </div>
  )
}

const Images = ({ images }: { images: ImageData[] }) => (
  <div
    className={cn(
      'grid max-w-xl gap-4',
      images.length > 1 ? 'grid-cols-2' : 'grid-cols-1'
    )}
  >
    {images.map((image) => (
      <ImageItem key={image.url} image={image} />
    ))}
  </div>
)

export default memo(Images)

Images.displayName = 'Images'
