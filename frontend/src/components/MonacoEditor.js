import { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import { motion } from "framer-motion";
import { Save, File, Code } from "lucide-react";

export const MonacoEditor = ({ file, onSave }) => {
  const [content, setContent] = useState("");
  const [isModified, setIsModified] = useState(false);
  const [language, setLanguage] = useState("plaintext");
  const editorRef = useRef(null);

  useEffect(() => {
    if (file) {
      setContent(file.content);
      setIsModified(false);
      setLanguage(getLanguageFromFileName(file.name));
    }
  }, [file]);

  const getLanguageFromFileName = (filename) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'css': 'css',
      'html': 'html',
      'json': 'json',
      'md': 'markdown',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
      'sql': 'sql',
      'sh': 'shell',
      'php': 'php',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust'
    };
    return languageMap[extension] || 'plaintext';
  };

  const handleContentChange = (value) => {
    setContent(value || "");
    setIsModified((value || "") !== (file?.content || ""));
  };

  const handleSave = () => {
    if (onSave && isModified && file) {
      onSave(content);
      setIsModified(false);
    }
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Configure Monaco editor theme
    monaco.editor.defineTheme('custom-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6b7280', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'f59e0b' },
        { token: 'string', foreground: '10b981' },
        { token: 'number', foreground: '3b82f6' },
        { token: 'function', foreground: '8b5cf6' },
      ],
      colors: {
        'editor.background': '#1f2937',
        'editor.foreground': '#e5e7eb',
        'editorLineNumber.foreground': '#6b7280',
        'editor.selectionBackground': '#3b82f6',
        'editor.lineHighlightBackground': '#374151',
      }
    });
    
    monaco.editor.setTheme('custom-dark');

    // Add keyboard shortcut for save (Ctrl+S / Cmd+S)
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      handleSave();
    });
  };

  if (!file) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-gray-800 border border-gray-700 rounded-lg h-full flex items-center justify-center"
      >
        <div className="text-center">
          <Code size={48} className="text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Select a file to start editing</p>
          <p className="text-gray-500 text-sm mt-2">Choose a file from the explorer to open it in the editor</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800 border border-gray-700 rounded-lg h-full flex flex-col"
    >
      {/* Editor Header */}
      <div className="border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <File size={16} className="text-blue-400" />
          <h3 className="text-sm font-medium text-white">{file.name}</h3>
          <span className="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">
            {language}
          </span>
          {isModified && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-2 h-2 bg-yellow-500 rounded-full"
            />
          )}
        </div>
        <div className="flex items-center space-x-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSave}
            disabled={!isModified}
            className={`flex items-center space-x-2 px-3 py-1 text-xs rounded transition-colors ${
              isModified
                ? "bg-green-600 hover:bg-green-700 text-white"
                : "bg-gray-600 text-gray-400 cursor-not-allowed"
            }`}
          >
            <Save size={12} />
            <span>Save</span>
          </motion.button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 relative">
        <Editor
          height="100%"
          language={language}
          value={content}
          onChange={handleContentChange}
          onMount={handleEditorDidMount}
          options={{
            theme: 'custom-dark',
            fontSize: 14,
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            lineNumbers: 'on',
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            insertSpaces: true,
            wordWrap: 'on',
            lineHeight: 1.5,
            padding: { top: 16, bottom: 16 },
            folding: true,
            showFoldingControls: 'always',
            renderLineHighlight: 'all',
            selectionHighlight: true,
            occurrencesHighlight: true,
            codeLens: true,
            contextmenu: true,
            mouseWheelZoom: true,
            multiCursorModifier: 'ctrlCmd',
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'full',
            bracketPairColorization: { enabled: true },
            guides: {
              bracketPairs: 'active',
              indentation: true
            },
            suggest: {
              showKeywords: true,
              showSnippets: true
            }
          }}
        />
      </div>

      {/* Editor Footer */}
      <div className="border-t border-gray-700 px-4 py-2 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center space-x-4">
          <span>Lines: {content.split('\n').length}</span>
          <span>Characters: {content.length}</span>
          <span>Size: {new Blob([content]).size} bytes</span>
        </div>
        <div className="flex items-center space-x-2">
          {isModified && (
            <motion.span 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-yellow-500"
            >
              Unsaved changes
            </motion.span>
          )}
          <span>UTF-8</span>
          <span className="capitalize">{language}</span>
        </div>
      </div>
    </motion.div>
  );
};