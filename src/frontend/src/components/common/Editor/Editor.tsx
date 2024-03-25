import React, { useEffect } from 'react';
import { useEditor, EditorContent, FloatingMenu, BubbleMenu } from '@tiptap/react';
import { Toolbar } from '@/components/common/Editor/Toolbar';
import StarterKit from '@tiptap/starter-kit';
import ListItem from '@tiptap/extension-list-item';
import BulletList from '@tiptap/extension-bullet-list';
import OrderedList from '@tiptap/extension-ordered-list';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Heading from '@tiptap/extension-heading';
import Document from '@tiptap/extension-document';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import './editorStyles.scss';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { useDispatch } from 'react-redux';
import { useAppSelector } from '@/types/reduxTypes';

type RichTextEditorProps = {
  editorHtmlContent: string;
  setEditorHtmlContent?: (content: string) => any;
  editable: boolean;
  isEditorEmpty?: (status: boolean) => void;
};

const extensions = [
  StarterKit,
  Document,
  Paragraph,
  Text,
  ListItem,
  BulletList,
  OrderedList,
  Heading,
  Link.configure({
    validate: (href) => /^https?:\/\//.test(href),
  }),
  Image.configure({
    inline: true,
  }),
];

const RichTextEditor = ({ editorHtmlContent, setEditorHtmlContent, editable, isEditorEmpty }: RichTextEditorProps) => {
  const dispatch = useDispatch();
  const editor = useEditor({
    extensions,
    content: editorHtmlContent,
    onUpdate: ({ editor }) => {
      setEditorHtmlContent && setEditorHtmlContent(editor.getHTML());
    },
    editable,
  });
  const clearEditorContent = useAppSelector((state) => state?.project?.clearEditorContent);

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
    <div className="fmtm-border-[1px] fmtm-border-gray-300 fmtm-rounded-md fmtm-bg-white">
      {editable && <Toolbar editor={editor} />}
      <EditorContent editor={editor} className={`${editable ? 'fmtm-min-h-[150px]' : 'fmtm-min-h-[50px]'}`} />
    </div>
  );
};

export default RichTextEditor;
