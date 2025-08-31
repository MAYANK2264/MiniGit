import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { GitCommit, GitBranch, User, Hash, Calendar, Plus, Minus, RotateCcw } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CommitGraph = ({ repoId }) => {
  const [commits, setCommits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCommit, setSelectedCommit] = useState(null);

  useEffect(() => {
    if (repoId) {
      fetchCommits();
    }
  }, [repoId]);

  const fetchCommits = async () => {
    try {
      const response = await axios.get(`${API}/repositories/${repoId}/commits`);
      setCommits(response.data);
    } catch (error) {
      console.error("Error fetching commits:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCommitClick = (commit) => {
    setSelectedCommit(selectedCommit?.id === commit.id ? null : commit);
  };

  if (loading) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg h-full flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
        <span className="ml-3 text-white">Loading commit history...</span>
      </div>
    );
  }

  if (commits.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-gray-800 border border-gray-700 rounded-lg h-full flex items-center justify-center"
      >
        <div className="text-center">
          <GitBranch size={48} className="text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No commits yet</h3>
          <p className="text-gray-400 mb-6">Start by making your first commit</p>
          <div className="bg-gray-700 rounded-lg p-4 text-left max-w-md">
            <p className="text-sm text-gray-300 mb-2">To make a commit:</p>
            <ol className="text-xs text-gray-400 space-y-1">
              <li>1. Create or edit files</li>
              <li>2. Go to the Files tab</li>
              <li>3. Click "New Commit" in the commit panel</li>
              <li>4. Add a commit message and author</li>
              <li>5. Click "Commit" to save your changes</li>
            </ol>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg h-full flex flex-col">
      <div className="border-b border-gray-700 px-4 py-3">
        <h3 className="text-sm font-medium text-white flex items-center space-x-2">
          <GitBranch size={16} className="text-green-400" />
          <span>Commit History ({commits.length})</span>
        </h3>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          {commits.map((commit, index) => (
            <motion.div
              key={commit.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative"
            >
              {/* Commit Line */}
              {index < commits.length - 1 && (
                <div className="absolute left-4 top-10 w-px h-16 bg-gray-600" />
              )}

              {/* Commit Node */}
              <motion.div
                whileHover={{ scale: 1.02 }}
                onClick={() => handleCommitClick(commit)}
                className="flex items-start space-x-4 p-4 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
              >
                <motion.div
                  whileHover={{ scale: 1.2 }}
                  className="w-8 h-8 bg-green-500 rounded-full flex-shrink-0 flex items-center justify-center relative z-10"
                >
                  <GitCommit size={16} className="text-white" />
                </motion.div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-white font-medium text-sm mb-1 truncate">
                        {commit.message}
                      </h4>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-400 mb-2">
                        <span className="flex items-center space-x-1">
                          <User size={10} />
                          <span>{commit.author}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Calendar size={10} />
                          <span>{new Date(commit.created_at).toLocaleDateString()}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Hash size={10} />
                          <span className="font-mono">{commit.commit_hash.substring(0, 7)}</span>
                        </span>
                      </div>

                      {/* Changes Summary */}
                      <div className="flex items-center space-x-3 text-xs">
                        {commit.changes_summary?.additions > 0 && (
                          <span className="flex items-center space-x-1 text-green-400">
                            <Plus size={10} />
                            <span>{commit.changes_summary.additions}</span>
                          </span>
                        )}
                        {commit.changes_summary?.deletions > 0 && (
                          <span className="flex items-center space-x-1 text-red-400">
                            <Minus size={10} />
                            <span>{commit.changes_summary.deletions}</span>
                          </span>
                        )}
                        {commit.changes_summary?.modifications > 0 && (
                          <span className="flex items-center space-x-1 text-yellow-400">
                            <RotateCcw size={10} />
                            <span>{commit.changes_summary.modifications}</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Commit Badge */}
                    <div className="flex items-center space-x-2">
                      {index === 0 && (
                        <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded">
                          HEAD
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {Object.keys(commit.files_snapshot || {}).length} files
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Expanded Commit Details */}
              {selectedCommit?.id === commit.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="ml-12 mt-2 bg-gray-900 rounded-lg p-4 border border-gray-600"
                >
                  <h5 className="text-white font-medium text-sm mb-3">Commit Details</h5>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wide">Full Hash</label>
                      <p className="text-sm text-gray-300 font-mono">{commit.commit_hash}</p>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wide">Author</label>
                      <p className="text-sm text-gray-300">{commit.author}</p>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wide">Date</label>
                      <p className="text-sm text-gray-300">
                        {new Date(commit.created_at).toLocaleString()}
                      </p>
                    </div>

                    {commit.parent_commits && commit.parent_commits.length > 0 && (
                      <div>
                        <label className="text-xs text-gray-400 uppercase tracking-wide">Parent Commits</label>
                        <div className="space-y-1">
                          {commit.parent_commits.map((parentHash) => (
                            <p key={parentHash} className="text-sm text-gray-300 font-mono">
                              {parentHash.substring(0, 7)}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {commit.files_snapshot && Object.keys(commit.files_snapshot).length > 0 && (
                      <div>
                        <label className="text-xs text-gray-400 uppercase tracking-wide">Files in this commit</label>
                        <div className="space-y-1 max-h-32 overflow-y-auto">
                          {Object.values(commit.files_snapshot).map((file, idx) => (
                            <div key={idx} className="flex items-center justify-between text-sm">
                              <span className="text-gray-300">{file.name}</span>
                              <span className="text-gray-500 text-xs font-mono">
                                {file.hash.substring(0, 7)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};