import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ====== COMPONENTS ======

const Header = () => {
  return (
    <header className="bg-gray-900 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">MG</span>
          </div>
          <h1 className="text-xl font-bold text-white">Mini-Git</h1>
        </Link>
        <nav className="flex items-center space-x-6">
          <Link to="/" className="text-gray-300 hover:text-white transition-colors">
            Repositories
          </Link>
          <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
            New Repository
          </button>
        </nav>
      </div>
    </header>
  );
};

const RepositoryCard = ({ repo, onClick }) => {
  return (
    <div 
      onClick={onClick}
      className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
            {repo.name}
          </h3>
          <p className="text-gray-400 mt-2 text-sm">
            {repo.description || "No description"}
          </p>
          <div className="flex items-center space-x-4 mt-4 text-xs text-gray-500">
            <span>{repo.file_count} files</span>
            <span>Created {new Date(repo.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <span className="text-xs text-gray-400">{repo.default_branch}</span>
        </div>
      </div>
    </div>
  );
};

const FileExplorer = ({ files, onFileSelect, selectedFile }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg">
      <div className="border-b border-gray-700 px-4 py-3">
        <h3 className="text-sm font-medium text-white">Files</h3>
      </div>
      <div className="p-2">
        {files.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>No files in this repository</p>
          </div>
        ) : (
          <div className="space-y-1">
            {files.map((file) => (
              <div
                key={file.id}
                onClick={() => onFileSelect(file)}
                className={`p-3 rounded-md cursor-pointer transition-colors ${
                  selectedFile?.id === file.id
                    ? "bg-blue-600 text-white"
                    : "hover:bg-gray-700 text-gray-300"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-blue-500 rounded-sm flex-shrink-0"></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">
                      {file.size} bytes • {new Date(file.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const FileEditor = ({ file, onSave, onChange }) => {
  const [content, setContent] = useState(file?.content || "");
  const [isModified, setIsModified] = useState(false);

  useEffect(() => {
    if (file) {
      setContent(file.content);
      setIsModified(false);
    }
  }, [file]);

  const handleContentChange = (e) => {
    const newContent = e.target.value;
    setContent(newContent);
    setIsModified(newContent !== file?.content);
    if (onChange) onChange(newContent);
  };

  const handleSave = () => {
    if (onSave && isModified) {
      onSave(content);
      setIsModified(false);
    }
  };

  if (!file) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg h-full flex items-center justify-center">
        <p className="text-gray-400">Select a file to edit</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg h-full flex flex-col">
      <div className="border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-medium text-white">{file.name}</h3>
          {isModified && (
            <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
          )}
        </div>
        <button
          onClick={handleSave}
          disabled={!isModified}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            isModified
              ? "bg-green-600 hover:bg-green-700 text-white"
              : "bg-gray-600 text-gray-400 cursor-not-allowed"
          }`}
        >
          Save
        </button>
      </div>
      <div className="flex-1 p-4">
        <textarea
          value={content}
          onChange={handleContentChange}
          className="w-full h-full bg-gray-900 text-gray-300 border border-gray-600 rounded p-3 font-mono text-sm resize-none focus:outline-none focus:border-blue-500"
          placeholder="Start typing..."
        />
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
        <div className="text-white">Loading repositories...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white">Your Repositories</h2>
            <p className="text-gray-400 mt-1">Manage your code repositories</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            New Repository
          </button>
        </div>

        {repositories.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📁</span>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No repositories yet</h3>
            <p className="text-gray-400 mb-6">Create your first repository to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors"
            >
              Create Repository
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {repositories.map((repo) => (
              <RepositoryCard
                key={repo.id}
                repo={repo}
                onClick={() => openRepository(repo)}
              />
            ))}
          </div>
        )}

        {/* Create Repository Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
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
                <button
                  onClick={createRepository}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors"
                >
                  Create Repository
                </button>
              </div>
            </div>
          </div>
        )}
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
  };

  const handleFileSave = async (content) => {
    if (!selectedFile) return;
    
    try {
      const response = await axios.put(
        `${API}/repositories/${repoId}/files/${selectedFile.id}`,
        { content }
      );
      
      // Update the file in the list
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
        <div className="text-white">Loading repository...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <main className="max-w-full px-6 py-6">
        {repository && (
          <div className="mb-6">
            <div className="flex items-center space-x-3 mb-2">
              <Link to="/" className="text-blue-400 hover:text-blue-300">
                Repositories
              </Link>
              <span className="text-gray-500">/</span>
              <h1 className="text-xl font-bold text-white">{repository.name}</h1>
            </div>
            <p className="text-gray-400">{repository.description}</p>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)]">
          {/* File Explorer - Left Sidebar */}
          <div className="col-span-3">
            <div className="mb-4">
              <button
                onClick={() => setShowCreateFile(true)}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm transition-colors"
              >
                New File
              </button>
            </div>
            <FileExplorer
              files={files}
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
            />
          </div>

          {/* File Editor - Main Content */}
          <div className="col-span-9">
            <FileEditor
              file={selectedFile}
              onSave={handleFileSave}
            />
          </div>
        </div>

        {/* Create File Modal */}
        {showCreateFile && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
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
                <button
                  onClick={createNewFile}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors"
                >
                  Create File
                </button>
              </div>
            </div>
          </div>
        )}
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