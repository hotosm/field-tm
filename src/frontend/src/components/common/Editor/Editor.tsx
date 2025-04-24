import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import { Toolbar } from '@/components/common/Editor/Toolbar';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import './editorStyles.scss';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

type RichTextEditorProps = {
  editorHtmlContent: string;
  setEditorHtmlContent?: (content: string) => any;
  editable: boolean;
  isEditorEmpty?: (status: boolean) => void;
  className?: string;
};

const extensions = [
  StarterKit,
  Link.configure({
    validate: (href) => /^https?:\/\//.test(href),
  }),
  Image.configure({
    inline: true,
  }),
];

const RichTextEditor = ({
  editorHtmlContent,
  setEditorHtmlContent,
  editable,
  isEditorEmpty,
  className,
}: RichTextEditorProps) => {
  const dispatch = useAppDispatch();
  const editor = useEditor({
    extensions,
    content: editorHtmlContent,
    onUpdate: ({ editor }) => {
      setEditorHtmlContent && setEditorHtmlContent(editor.getHTML());
    },
    editable,
  });

  const clearEditorContent = useAppSelector((state) => state?.project?.clearEditorContent);

  // on first render set content to editor if initial content present
  useEffect(() => {
    if (editor && editorHtmlContent && editor.isEmpty) {
      editor.commands.setContent(editorHtmlContent);
    }
  }, [editorHtmlContent, editor]);

  useEffect(() => {
    if (editable && clearEditorContent) {
      editor?.commands.clearContent(true);
      dispatch(ProjectActions.ClearEditorContent(false));
    }
  }, [clearEditorContent]);

  useEffect(() => {
    if (isEditorEmpty) {
      if (typeof editor?.isEmpty === 'undefined') {
        isEditorEmpty(true);
        return;
      }
      isEditorEmpty(editor?.isEmpty);
    }
  }, [editorHtmlContent]);

  if (!editor) {
    return null;
  }

  return (
    <div className={`fmtm-border-[1px] fmtm-border-gray-300 fmtm-rounded-md fmtm-bg-white ${className}`}>
      {editable && <Toolbar editor={editor} />}
      <EditorContent editor={editor} className={`${editable ? 'fmtm-min-h-[150px] fmtm-p-4' : 'fmtm-min-h-[50px]'}`} />
    </div>
  );
};

export default RichTextEditor;
