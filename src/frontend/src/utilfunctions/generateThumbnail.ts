export const generateThumbnail = ({
  file,
  maxWidth,
  maxHeight,
}: {
  file: File;
  maxWidth: number;
  maxHeight: number;
}): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();

      if (e.target?.result) {
        img.src = e.target.result as string;

        img.onload = () => {
          // Create canvas for thumbnail generation
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          if (!ctx) {
            reject(new Error('Failed to get canvas context.'));
            return;
          }

          // Scale the image proportionally
          const scale = Math.min(maxWidth / img.width, maxHeight / img.height);
          const resizedWidth = img.width * scale;
          const resizedHeight = img.height * scale;

          canvas.width = resizedWidth;
          canvas.height = resizedHeight;

          ctx.drawImage(img, 0, 0, resizedWidth, resizedHeight);

          // Generate thumbnail as Data URL
          const thumbnail = canvas.toDataURL();
          resolve(thumbnail);
        };

        img.onerror = () => reject(new Error('Failed to load image.'));
      } else {
        reject(new Error('Invalid file result.'));
      }
    };

    reader.onerror = () => reject(new Error('Failed to read file.'));
    reader.readAsDataURL(file);
  });
};
