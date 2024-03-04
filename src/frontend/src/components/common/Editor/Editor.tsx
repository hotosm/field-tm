import React, { useState } from 'react';
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

type RichTextEditorProps = {
  editorHtmlContent: string;
  setEditorHtmlContent?: (content: string) => any;
  editable: boolean;
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

const RichTextEditor = ({ editorHtmlContent, setEditorHtmlContent, editable }: RichTextEditorProps) => {
  const editor = useEditor({
    extensions,
    content: editorHtmlContent,
    onUpdate: ({ editor }) => {
      setEditorHtmlContent && setEditorHtmlContent(editor.getHTML());
    },
    editable,
  });

  if (!editor) {
    return null;
  }

  return (
    <div className="no-tailwindcss fmtm-remove-all fmtm-border-[1px] fmtm-border-gray-300 fmtm-rounded-md fmtm-bg-white">
      {editable && <Toolbar editor={editor} />}
      <EditorContent editor={editor} />
    </div>
  );
};

export default RichTextEditor;
