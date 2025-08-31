import { motion, AnimatePresence } from "framer-motion";
import { File, Folder, FolderOpen, Code, FileText, Image } from "lucide-react";

export const FileTree = ({ files, onFileSelect, selectedFile }) => {
  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    const iconMap = {
      'js': Code,
      'jsx': Code,
      'ts': Code,
      'tsx': Code,
      'py': Code,
      'java': Code,
      'cpp': Code,
      'c': Code,
      'html': Code,
      'css': Code,
      'json': Code,
      'xml': Code,
      'md': FileText,
      'txt': FileText,
      'readme': FileText,
      'png': Image,
      'jpg': Image,
      'jpeg': Image,
      'gif': Image,
      'svg': Image
    };
    
    return iconMap[extension] || File;
  };

  const getFileColor = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    const colorMap = {
      'js': 'text-yellow-400',
      'jsx': 'text-blue-400', 
      'ts': 'text-blue-500',
      'tsx': 'text-blue-400',
      'py': 'text-green-400',
      'java': 'text-orange-400',
      'cpp': 'text-blue-600',
      'c': 'text-blue-600',
      'html': 'text-orange-500',
      'css': 'text-blue-400',
      'json': 'text-yellow-500',
      'xml': 'text-green-500',
      'md': 'text-white',
      'txt': 'text-gray-400',
      'png': 'text-purple-400',
      'jpg': 'text-purple-400',
      'jpeg': 'text-purple-400',
      'gif': 'text-purple-400',
      'svg': 'text-purple-500'
    };
    
    return colorMap[extension] || 'text-gray-300';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-gray-800 border border-gray-700 rounded-lg"
    >
      <div className="border-b border-gray-700 px-4 py-3">
        <h3 className="text-sm font-medium text-white flex items-center space-x-2">
          <FolderOpen size={16} className="text-blue-400" />
          <span>Files ({files.length})</span>
        </h3>
      </div>
      
      <div className="p-2 max-h-96 overflow-y-auto">
        {files.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-8 text-gray-400"
          >
            <Folder size={32} className="mx-auto mb-3 text-gray-600" />
            <p className="text-sm">No files in this repository</p>
            <p className="text-xs mt-1">Create a new file to get started</p>
          </motion.div>
        ) : (
          <AnimatePresence>
            <div className="space-y-1">
              {files.map((file, index) => {
                const IconComponent = getFileIcon(file.name);
                const colorClass = getFileColor(file.name);
                const isSelected = selectedFile?.id === file.id;
                
                return (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => onFileSelect(file)}
                    className={`p-3 rounded-md cursor-pointer transition-all duration-200 group ${
                      isSelected
                        ? "bg-blue-600 text-white shadow-lg"
                        : "hover:bg-gray-700 text-gray-300"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <motion.div
                        whileHover={{ scale: 1.1 }}
                        className={`flex-shrink-0 ${
                          isSelected ? 'text-white' : colorClass
                        }`}
                      >
                        <IconComponent size={16} />
                      </motion.div>
                      
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${
                          isSelected ? 'text-white' : 'text-gray-200'
                        }`}>
                          {file.name}
                        </p>
                        <div className={`flex items-center space-x-2 text-xs ${
                          isSelected ? 'text-blue-100' : 'text-gray-400'
                        }`}>
                          <span>{file.size} bytes</span>
                          <span>•</span>
                          <span>{new Date(file.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0, rotate: -180 }}
                          animate={{ scale: 1, rotate: 0 }}
                          className="w-2 h-2 bg-white rounded-full"
                        />
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </AnimatePresence>
        )}
      </div>
    </motion.div>
  );
};