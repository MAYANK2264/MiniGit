import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { MonacoEditor } from "./components/MonacoEditor";
import { CommitGraph } from "./components/CommitGraph";
import { FileTree } from "./components/FileTree";
import { 
  GitBranch, 
  GitCommit, 
  File, 
  Folder, 
  Plus, 
  Save, 
  Upload,
  Calendar,
  User,
  Hash
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ====== COMPONENTS ======

const Header = () => {
  return (
    <motion.header 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-gray-900 border-b border-gray-700 px-6 py-4"
    >
      <div className="flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3">
          <motion.div 
            whileHover={{ scale: 1.1 }}
            className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center"
          >
            <span className="text-white font-bold text-sm">MG</span>
          </motion.div>
          <h1 className="text-xl font-bold text-white">Mini-Git</h1>
        </Link>
        <nav className="flex items-center space-x-6">
          <Link to="/" className="text-gray-300 hover:text-white transition-colors flex items-center space-x-2">
            <GitBranch size={16} />
            <span>Repositories</span>
          </Link>
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Plus size={16} />
            <span>New Repository</span>
          </motion.button>
        </nav>
      </div>
    </motion.header>
  );
};

const RepositoryCard = ({ repo, onClick }) => {
  return (
    <motion.div 
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors flex items-center space-x-2">
            <Folder size={20} />
            <span>{repo.name}</span>
          </h3>
          <p className="text-gray-400 mt-2 text-sm">
            {repo.description || "No description"}
          </p>
          <div className="flex items-center space-x-4 mt-4 text-xs text-gray-500">
            <span className="flex items-center space-x-1">
              <File size={12} />
              <span>{repo.file_count} files</span>
            </span>
            <span className="flex items-center space-x-1">
              <Calendar size={12} />
              <span>Created {new Date(repo.created_at).toLocaleDateString()}</span>
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-400">{repo.default_branch}</span>
        </div>
      </div>
    </motion.div>
  );
};

const CommitPanel = ({ repoId, onCommitCreated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [commits, setCommits] = useState([]);
  const [newCommit, setNewCommit] = useState({ message: "", author: "Anonymous" });
  const [loading, setLoading] = useState(false);

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
    }
  };

  const createCommit = async () => {
    if (!newCommit.message.trim()) return;
    
    setLoading(true);
    try {
      await axios.post(`${API}/repositories/${repoId}/commit`, newCommit);
      setNewCommit({ message: "", author: "Anonymous" });
      setIsOpen(false);
      await fetchCommits();
      if (onCommitCreated) onCommitCreated();
    } catch (error) {
      console.error("Error creating commit:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg">
      <div className="border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-white flex items-center space-x-2">
          <GitCommit size={16} />
          <span>Commits ({commits.length})</span>
        </h3>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(!isOpen)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors"
        >
          New Commit
        </motion.button>
      </div>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-gray-700 p-4 overflow-hidden"
          >
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Commit Message
                </label>
                <input
                  type="text"
                  value={newCommit.message}
                  onChange={(e) => setNewCommit({ ...newCommit, message: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Add a commit message..."
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Author
                </label>
                <input
                  type="text"
                  value={newCommit.author}
                  onChange={(e) => setNewCommit({ ...newCommit, author: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Your name"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-3 py-1 text-gray-400 hover:text-white transition-colors text-sm"
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={createCommit}
                  disabled={loading || !newCommit.message.trim()}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-3 py-1 rounded text-sm transition-colors"
                >
                  {loading ? "Creating..." : "Commit"}
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="max-h-64 overflow-y-auto">
        {commits.length === 0 ? (
          <div className="p-4 text-center text-gray-400 text-sm">
            No commits yet. Create your first commit!
          </div>
        ) : (
          <div className="p-2">
            {commits.map((commit) => (
              <motion.div
                key={commit.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-3 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-500 rounded-full flex-shrink-0 flex items-center justify-center">
                    <GitCommit size={12} className="text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-medium truncate">
                      {commit.message}
                    </p>
                    <div className="flex items-center space-x-4 mt-1 text-xs text-gray-400">
                      <span className="flex items-center space-x-1">
                        <User size={10} />
                        <span>{commit.author}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Hash size={10} />
                        <span>{commit.commit_hash.substring(0, 7)}</span>
                      </span>
                      <span>{new Date(commit.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      +{commit.changes_summary?.additions || 0} -{commit.changes_summary?.deletions || 0} ~{commit.changes_summary?.modifications || 0}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ====== PAGES ======

const Home = () => {
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRepo, setNewRepo] = useState({ name: "", description: "" });
  const navigate = useNavigate();

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    try {
      const response = await axios.get(`${API}/repositories`);
      setRepositories(response.data);
    } catch (error) {
      console.error("Error fetching repositories:", error);
    } finally {
      setLoading(false);
    }
  };

  const createRepository = async () => {
    if (!newRepo.name.trim()) return;
    
    try {
      const response = await axios.post(`${API}/repositories`, newRepo);
      setRepositories([...repositories, response.data]);
      setNewRepo({ name: "", description: "" });
      setShowCreateModal(false);
    } catch (error) {
      console.error("Error creating repository:", error);
    }
  };

  const openRepository = (repo) => {
    navigate(`/repo/${repo.id}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
        <span className="ml-3 text-white">Loading repositories...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h2 className="text-2xl font-bold text-white">Your Repositories</h2>
            <p className="text-gray-400 mt-1">Manage your code repositories with version control</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowCreateModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Plus size={16} />
            <span>New Repository</span>
          </motion.button>
        </motion.div>

        {repositories.length === 0 ? (
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-center py-16"
          >
            <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Folder size={32} className="text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No repositories yet</h3>
            <p className="text-gray-400 mb-6">Create your first repository to start version control</p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowCreateModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2 mx-auto"
            >
              <Plus size={16} />
              <span>Create Repository</span>
            </motion.button>
          </motion.div>
        ) : (
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {repositories.map((repo) => (
              <RepositoryCard
                key={repo.id}
                repo={repo}
                onClick={() => openRepository(repo)}
              />
            ))}
          </motion.div>
        )}

        {/* Create Repository Modal */}
        <AnimatePresence>
          {showCreateModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-backdrop"
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4"
              >
                <h3 className="text-lg font-bold text-white mb-4">Create New Repository</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Repository Name
                    </label>
                    <input
                      type="text"
                      value={newRepo.name}
                      onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      placeholder="my-awesome-project"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Description (optional)
                    </label>
                    <textarea
                      value={newRepo.description}
                      onChange={(e) => setNewRepo({ ...newRepo, description: e.target.value })}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      rows="3"
                      placeholder="A brief description of your project"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={createRepository}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors"
                  >
                    Create Repository
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
};

const RepositoryView = () => {
  const { repoId } = useParams();
  const [repository, setRepository] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateFile, setShowCreateFile] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [activeTab, setActiveTab] = useState("files");

  useEffect(() => {
    if (repoId) {
      fetchRepository();
      fetchFiles();
    }
  }, [repoId]);

  const fetchRepository = async () => {
    try {
      const response = await axios.get(`${API}/repositories/${repoId}`);
      setRepository(response.data);
    } catch (error) {
      console.error("Error fetching repository:", error);
    }
  };

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API}/repositories/${repoId}/files`);
      setFiles(response.data);
    } catch (error) {
      console.error("Error fetching files:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setActiveTab("files");
  };

  const handleFileSave = async (content) => {
    if (!selectedFile) return;
    
    try {
      const response = await axios.put(
        `${API}/repositories/${repoId}/files/${selectedFile.id}`,
        { content }
      );
      
      const updatedFiles = files.map(f => 
        f.id === selectedFile.id ? response.data : f
      );
      setFiles(updatedFiles);
      setSelectedFile(response.data);
    } catch (error) {
      console.error("Error saving file:", error);
    }
  };

  const createNewFile = async () => {
    if (!newFileName.trim()) return;
    
    try {
      const response = await axios.post(`${API}/repositories/${repoId}/files`, {
        name: newFileName,
        content: ""
      });
      
      setFiles([...files, response.data]);
      setSelectedFile(response.data);
      setNewFileName("");
      setShowCreateFile(false);
    } catch (error) {
      console.error("Error creating file:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
        <span className="ml-3 text-white">Loading repository...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <main className="max-w-full px-6 py-6">
        {repository && (
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mb-6"
          >
            <div className="flex items-center space-x-3 mb-2">
              <Link to="/" className="text-blue-400 hover:text-blue-300 flex items-center space-x-1">
                <GitBranch size={16} />
                <span>Repositories</span>
              </Link>
              <span className="text-gray-500">/</span>
              <h1 className="text-xl font-bold text-white flex items-center space-x-2">
                <Folder size={20} />
                <span>{repository.name}</span>
              </h1>
            </div>
            <p className="text-gray-400">{repository.description}</p>
          </motion.div>
        )}

        {/* Tab Navigation */}
        <div className="flex items-center space-x-1 mb-6">
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={() => setActiveTab("files")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === "files" 
                ? "bg-blue-600 text-white" 
                : "text-gray-400 hover:text-white"
            }`}
          >
            Files
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={() => setActiveTab("commits")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === "commits" 
                ? "bg-blue-600 text-white" 
                : "text-gray-400 hover:text-white"
            }`}
          >
            Commits
          </motion.button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "files" && (
            <motion.div
              key="files"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="grid grid-cols-12 gap-6 h-[calc(100vh-250px)]"
            >
              {/* File Explorer - Left Sidebar */}
              <div className="col-span-3">
                <div className="mb-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowCreateFile(true)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm transition-colors flex items-center justify-center space-x-2"
                  >
                    <Plus size={16} />
                    <span>New File</span>
                  </motion.button>
                </div>
                <FileTree
                  files={files}
                  onFileSelect={handleFileSelect}
                  selectedFile={selectedFile}
                />
              </div>

              {/* File Editor - Main Content */}
              <div className="col-span-6">
                <MonacoEditor
                  file={selectedFile}
                  onSave={handleFileSave}
                />
              </div>

              {/* Commit Panel - Right Sidebar */}
              <div className="col-span-3">
                <CommitPanel 
                  repoId={repoId} 
                  onCommitCreated={fetchFiles}
                />
              </div>
            </motion.div>
          )}

          {activeTab === "commits" && (
            <motion.div
              key="commits"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-[calc(100vh-250px)]"
            >
              <CommitGraph repoId={repoId} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Create File Modal */}
        <AnimatePresence>
          {showCreateFile && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-backdrop"
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4"
              >
                <h3 className="text-lg font-bold text-white mb-4">Create New File</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    File Name
                  </label>
                  <input
                    type="text"
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="example.txt"
                  />
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateFile(false)}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={createNewFile}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors"
                  >
                    Create File
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
};

// ====== MAIN APP ======

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/repo/:repoId" element={<RepositoryView />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;