import React from 'react';
import RichTextEditor from '@/components/common/Editor/Editor';

const Instructions = ({ instructions }: { instructions: string }) => {
  return (
    <div className="fmtm-overflow-y-scroll scrollbar">
      {instructions ? (
        <RichTextEditor editorHtmlContent={instructions} editable={false} />
      ) : (
        <p className="fmtm-mt-5 fmtm-text-center fmtm-text-xl fmtm-text-gray-400">No Instructions!</p>
      )}
    </div>
  );
};

export default Instructions;
