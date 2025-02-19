import React, { useCallback, useEffect, useState } from 'react';
import { Editor } from '@tiptap/react';
import AssetModules from '@/shared/AssetModules';
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '../Dropdown';
import { Tooltip } from '@mui/material';
import InputTextField from '@/components/common/InputTextField';
import Button from '@/components/common/Button';

type ToolbarProps = {
  editor: Editor | null;
};

const iconClassName =
  'fmtm-duration-300 hover:fmtm-bg-red-100 fmtm-rounded fmtm-cursor-pointer fmtm-p-[2px] fmtm-w-fit';

export const Toolbar = ({ editor }: ToolbarProps) => {
  const [linkText, setLinkText] = useState('');
  const [linkDropdownOpen, setLinkDropdownOpen] = useState(false);
  const [imageURL, setImageURL] = useState('');
  const [imageDropdownOpen, setImageDropdownOpen] = useState(false);

  const isEditorActive = (editorItem: string) => {
    if (editor?.isActive(editorItem)) {
      return 'fmtm-text-primaryRed fmtm-bg-red-100';
    }
    return '';
  };

  // set link if a link is already linked
  const previousUrl = editor?.getAttributes('link').href;
  useEffect(() => {
    if (previousUrl) {
      setLinkText(previousUrl);
    }
  }, [previousUrl]);

  const setLink = useCallback(() => {
    const url = linkText;
    // cancelled
    if (url === null) {
      return;
    }
    // empty
    if (url === '') {
      editor?.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }
    // update link
    editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
    setLinkText('');
    setLinkDropdownOpen(false);
  }, [editor, linkText]);

  // add image to editor
  const addImage = useCallback(() => {
    if (imageURL) {
      editor?.chain().focus().setImage({ src: imageURL }).run();
    }
    setImageURL('');
  }, [editor, imageURL]);

  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-px-2 fmtm-border-b-[1px] fmtm-border-gray-300">
      <div className="fmtm-flex fmtm-flex-wrap fmtm-gap-2 fmtm-py-1 fmtm-items-center">
        <Tooltip title="Bold">
          <AssetModules.FormatBoldIcon
            onClick={() => editor?.chain().focus().toggleBold().run()}
            className={`${iconClassName} ${isEditorActive('bold')}`}
          />
        </Tooltip>
        <Tooltip title="Italic">
          <AssetModules.FormatItalicIcon
            onClick={() => editor?.chain().focus().toggleItalic().run()}
            className={`${iconClassName} ${isEditorActive('italic')}`}
          />
        </Tooltip>
        <Tooltip title="Strike">
          <AssetModules.StrikethroughSIcon
            onClick={() => editor?.chain().focus().toggleStrike().run()}
            className={`${iconClassName} ${isEditorActive('strike')}`}
          />
        </Tooltip>
        <DropdownMenu>
          <DropdownMenuTrigger className="fmtm-outline-none fmtm-w-fit">
            <Tooltip title="Heading">
              <div
                className={`fmtm-font-bold fmtm-font-archivo fmtm-scale-110 ${iconClassName} !fmtm-py-0 fmtm-px-2 ${isEditorActive(
                  'heading',
                )}`}
              >
                h
              </div>
            </Tooltip>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="fmtm-flex fmtm-gap-1 fmtm-bg-white fmtm-px-1 fmtm-z-[10005]">
            <Tooltip title="Heading 1">
              <p
                onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
                className={`${iconClassName} fmtm-px-2 ${
                  editor?.isActive('heading', { level: 1 }) ? 'fmtm-text-primaryRed fmtm-bg-red-100' : ''
                }`}
              >
                H<sub>1</sub>
              </p>
            </Tooltip>

            <Tooltip title="Heading 2">
              <p
                onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
                className={`${iconClassName} fmtm-px-2 ${
                  editor?.isActive('heading', { level: 2 }) ? 'fmtm-text-primaryRed fmtm-bg-red-100' : ''
                }`}
              >
                H<sub>2</sub>
              </p>
            </Tooltip>

            <Tooltip title="Heading 3">
              <p
                onClick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
                className={`${iconClassName} fmtm-px-2 ${
                  editor?.isActive('heading', { level: 3 }) ? 'fmtm-text-primaryRed fmtm-bg-red-100' : ''
                }`}
              >
                H<sub>3</sub>
              </p>
            </Tooltip>
          </DropdownMenuContent>
        </DropdownMenu>
        <Tooltip title="Unordered List">
          <AssetModules.ListViewIcon
            onClick={() => editor?.chain().focus().toggleBulletList().run()}
            className={`${iconClassName} ${isEditorActive('bulletList')}`}
          />
        </Tooltip>
        <Tooltip title="Numbered List">
          <AssetModules.FormatListNumberedIcon
            onClick={() => editor?.chain().focus().toggleOrderedList().run()}
            className={`${iconClassName} ${isEditorActive('orderedList')}`}
          />
        </Tooltip>
        <Tooltip title="Code">
          <AssetModules.CodeIcon
            onClick={() => editor?.chain().focus().toggleCodeBlock().run()}
            className={`${iconClassName} ${isEditorActive('codeBlock')}`}
          />
        </Tooltip>
        <DropdownMenu
          open={linkDropdownOpen}
          onOpenChange={(state) => {
            setLinkDropdownOpen(state);
            if (!state) {
              setLinkText('');
            }
          }}
        >
          <DropdownMenuTrigger className="fmtm-outline-none fmtm-w-fit">
            <Tooltip title="Link">
              <AssetModules.LinkIcon className={`${iconClassName} ${isEditorActive('link')}`} />
            </Tooltip>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="fmtm-z-[10005] fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-bg-white">
            <InputTextField
              placeholder="URL"
              onChange={(e) => {
                setLinkText(e.target.value);
              }}
              value={linkText}
              fieldType="text"
            />
            <Button variant="primary-red" onClick={setLink}>
              Add
            </Button>
          </DropdownMenuContent>
        </DropdownMenu>
        <Tooltip title="Quote">
          <AssetModules.FormatQuoteIcon
            onClick={() => editor?.chain().focus().toggleBlockquote().run()}
            className={`${iconClassName} ${isEditorActive('blockquote')}`}
          />
        </Tooltip>
        <Tooltip title="Horizontal Ruler">
          <AssetModules.HorizontalRuleIcon
            onClick={() => editor?.chain().focus().setHorizontalRule().run()}
            className={`${iconClassName}`}
          />
        </Tooltip>
        <DropdownMenu open={imageDropdownOpen} onOpenChange={(state) => setImageDropdownOpen(state)}>
          <DropdownMenuTrigger className="fmtm-outline-none fmtm-w-fit">
            <Tooltip title="Image">
              <AssetModules.ImageAddIcon className={`${iconClassName}`} />
            </Tooltip>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="fmtm-z-[10005] fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-bg-white">
            <InputTextField
              placeholder="Image URL"
              onChange={(e) => {
                setImageURL(e.target.value);
              }}
              value={imageURL}
              fieldType="text"
            />
            <Button variant="primary-red" onClick={addImage}>
              Insert
            </Button>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="fmtm-flex fmtm-gap-2 fmtm-py-1">
        <Tooltip title="Undo">
          <AssetModules.UndoIcon onClick={() => editor?.chain().focus().undo().run()} className={`${iconClassName}`} />
        </Tooltip>
        <Tooltip title="Redo">
          <AssetModules.RedoIcon onClick={() => editor?.chain().focus().redo().run()} className={`${iconClassName}`} />
        </Tooltip>
      </div>
    </div>
  );
};
