import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  DocumentTextIcon,
  CalendarIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  CloudArrowUpIcon,
  TrashIcon,
  PencilIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import { useNotificationContext } from '../contexts/NotificationContext';
import Header from '../components/Header.js';
import Footer from '../components/Footer.js';
import { downloadFileFromUrl } from '../utils/downloadFile';

interface Constitution {
  id: number;
  title: string;
  year?: number;
  filename: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

const ConstitutionsPage: React.FC = () => {
  const navigate = useNavigate();
  
  // Déplacer l'appel du hook au début, sans condition
  const notificationContext = useNotificationContext();
  const { showSuccess, showError, showWarning } = notificationContext;
  
  const [constitutions, setConstitutions] = useState<Constitution[]>([]);
  const [filteredConstitutions, setFilteredConstitutions] = useState<Constitution[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingConstitution, setDeletingConstitution] = useState<Constitution | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingConstitution, setEditingConstitution] = useState<Constitution | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Extraire les années uniques des constitutions
  const years = [...new Set(constitutions.map(c => c.year).filter(Boolean))].sort((a, b) => (b || 0) - (a || 0));

  // Fonction pour filtrer les constitutions
  const filterConstitutions = () => {
    let filtered = constitutions;

    // Filtre par recherche
    if (searchQuery) {
      filtered = filtered.filter(constitution =>
        constitution.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        constitution.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filtre par année
    if (selectedYear) {
      filtered = filtered.filter(constitution => constitution.year === parseInt(selectedYear));
    }

    setFilteredConstitutions(filtered);
  };

  // Appliquer les filtres quand les constitutions ou les filtres changent
  useEffect(() => {
    filterConstitutions();
  }, [constitutions, searchQuery, selectedYear]);

  const fetchConstitutions = async () => {
    console.log('ConstitutionsPage - fetchConstitutions - Début');
    try {
      console.log('ConstitutionsPage - fetchConstitutions - Appel API');
      const response = await axios.get('/api/constitutions/');
      console.log('ConstitutionsPage - fetchConstitutions - Réponse complète:', response);
      console.log('ConstitutionsPage - fetchConstitutions - Données:', response.data);
      console.log('ConstitutionsPage - fetchConstitutions - Type de données:', typeof response.data);
      console.log('ConstitutionsPage - fetchConstitutions - Longueur:', response.data.length);
      
      if (Array.isArray(response.data)) {
        setConstitutions(response.data);
        console.log('ConstitutionsPage - fetchConstitutions - Constitutions mises à jour:', response.data.length);
      } else {
        console.error('ConstitutionsPage - fetchConstitutions - Données non-array:', response.data);
        setConstitutions([]);
      }
      setLoading(false);
    } catch (error: any) {
      console.error('ConstitutionsPage - fetchConstitutions - Erreur complète:', error);
      console.error('ConstitutionsPage - fetchConstitutions - Message d\'erreur:', error.message);
      console.error('ConstitutionsPage - fetchConstitutions - Status:', error.response?.status);
      console.error('ConstitutionsPage - fetchConstitutions - Data:', error.response?.data);
      setConstitutions([]);
      setLoading(false);
    }
  };

  const handleAnalyzeFiles = async () => {
    setAnalyzing(true);
    try {
      const response = await axios.post('/api/constitutions/analyze-files');
      showSuccess('Analyse terminée', 'Les fichiers ont été analysés avec succès.');
      await fetchConstitutions(); // Recharger les constitutions
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error);
      showError('Erreur d\'analyse', 'Une erreur est survenue lors de l\'analyse des fichiers.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUploadFromDrop = async (file: File) => {
    // Vérifications préalables
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showWarning('Type de fichier invalide', 'Veuillez sélectionner un fichier PDF.');
      return;
    }

    // Vérifier la taille du fichier (16MB max)
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
      showWarning('Fichier trop volumineux', 'La taille maximale autorisée est de 16MB.');
      return;
    }

    setSelectedFile(file);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Vérifications préalables
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showWarning('Type de fichier invalide', 'Veuillez sélectionner un fichier PDF.');
      return;
    }

    // Vérifier la taille du fichier (16MB max)
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
      showWarning('Fichier trop volumineux', 'La taille maximale autorisée est de 16MB.');
      return;
    }

    setSelectedFile(file);
  };

  const handleSaveFile = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      console.log('Upload du fichier:', selectedFile.name, 'Taille:', selectedFile.size);
      
      const response = await axios.post('/api/constitutions/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
        timeout: 60000, // 60 secondes de timeout
      });

      console.log('Upload réussi:', response.data);
      showSuccess('Fichier uploadé avec succès', `Le fichier "${selectedFile.name}" a été uploadé et analysé.`);
      setShowUploadModal(false);
      setSelectedFile(null);
      
      // Réinitialiser l'input file
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Recharger les constitutions
      await fetchConstitutions();
      
    } catch (error: any) {
      console.error('Erreur lors de l\'upload:', error);
      
      let errorMessage = 'Une erreur est survenue lors de l\'upload du fichier.';
      
      if (error.response) {
        // Erreur de réponse du serveur
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 400) {
          errorMessage = data.detail || 'Fichier invalide. Vérifiez le format et la taille.';
        } else if (status === 413) {
          errorMessage = 'Fichier trop volumineux. Taille maximale : 16MB.';
        } else if (status === 500) {
          errorMessage = 'Erreur serveur. Veuillez réessayer.';
        } else {
          errorMessage = data.detail || `Erreur ${status}: ${data.message || 'Erreur inconnue'}`;
        }
      } else if (error.request) {
        // Erreur de réseau
        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet.';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Délai d\'attente dépassé. Le fichier est peut-être trop volumineux.';
      }
      
      showError('Erreur d\'upload', errorMessage);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };



  const handleDeleteConstitution = async (constitution: Constitution) => {
    setDeleting(true);
    try {
              await axios.delete(`/api/constitutions/${constitution.id}`);
      showSuccess('Constitution supprimée', 'La constitution a été supprimée avec succès.');
      setShowDeleteModal(false);
      setDeletingConstitution(null);
      await fetchConstitutions();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      showError('Erreur de suppression', 'Une erreur est survenue lors de la suppression.');
    } finally {
      setDeleting(false);
    }
  };

  const handleEditConstitution = async (updatedConstitution: Partial<Constitution>) => {
    if (!editingConstitution) return;

    try {
              await axios.put(`/api/constitutions/${editingConstitution.id}`, updatedConstitution);
      showSuccess('Constitution mise à jour', 'La constitution a été mise à jour avec succès.');
      setShowEditModal(false);
      setEditingConstitution(null);
      await fetchConstitutions();
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      showError('Erreur de mise à jour', 'Une erreur est survenue lors de la mise à jour.');
    }
  };

  useEffect(() => {
    fetchConstitutions();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement des constitutions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 sm:mb-8 gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Constitutions de la Guinée
          </h1>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 w-full sm:w-auto">
            <button
              onClick={handleAnalyzeFiles}
              disabled={analyzing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-3 sm:px-4 py-2 rounded-lg flex items-center justify-center space-x-2 text-sm sm:text-base"
            >
              {analyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span className="hidden sm:inline">Analyse en cours...</span>
                  <span className="sm:hidden">Analyse...</span>
                </>
              ) : (
                <>
                  <DocumentTextIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="hidden sm:inline">Analyser les fichiers</span>
                  <span className="sm:hidden">Analyser</span>
                </>
              )}
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-3 sm:px-4 py-2 rounded-lg flex items-center justify-center space-x-2 text-sm sm:text-base"
            >
              <PlusIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden sm:inline">Ajouter un fichier PDF</span>
              <span className="sm:hidden">Ajouter PDF</span>
            </button>
          </div>
        </div>

        {/* Barre de recherche et filtres */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                placeholder="Rechercher une constitution..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <FunnelIcon className="h-5 w-5" />
              <span>Filtres</span>
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 p-4 bg-white rounded-lg shadow border">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Année
                  </label>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Toutes les années</option>
                    {years.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Statistiques */}
        <div className="mb-6">
              <p className="text-gray-600">
            {filteredConstitutions.length} constitution(s) trouvée(s)
          </p>
        </div>

        {/* Liste des constitutions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {filteredConstitutions.length === 0 ? (
            <div className="col-span-full text-center py-8">
              <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucune constitution trouvée</p>
            </div>
          ) : (
            filteredConstitutions.map((constitution) => (
              <div key={constitution.id} className="bg-white rounded-lg shadow-md p-4 sm:p-6 flex flex-col min-h-[240px] sm:min-h-[280px]">
                {/* Header avec titre et boutons d'action */}
                <div className="flex justify-between items-start mb-3 sm:mb-4">
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900 flex-1 pr-2 line-clamp-2">
                    {constitution.title}
                  </h3>
                  <div className="flex space-x-1 sm:space-x-2 flex-shrink-0 ml-2">
                    <button
                      onClick={() => {
                        setEditingConstitution(constitution);
                        setShowEditModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50 transition-colors"
                    >
                      <PencilIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                    </button>
                    <button
                      onClick={() => {
                        setDeletingConstitution(constitution);
                        setShowDeleteModal(true);
                      }}
                      className="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50 transition-colors"
                    >
                      <TrashIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                    </button>
                  </div>
                </div>

                {/* Contenu principal - prend l'espace disponible */}
                <div className="flex-1 space-y-2 sm:space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-0">
                    <p className="text-sm sm:text-base text-gray-600">
                      <span className="font-medium">Année:</span> {constitution.year || 'Non spécifiée'}
                    </p>
                  </div>
                  
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-0">
                    <p className="text-sm sm:text-base text-gray-600">
                      <span className="font-medium">Statut:</span> 
                      <span className={`ml-1 px-2 py-1 text-xs rounded-full ${
                        constitution.status === 'active' ? 'bg-green-100 text-green-800' :
                        constitution.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                        constitution.status === 'archived' ? 'bg-gray-100 text-gray-800' :
                        constitution.status === 'in_development' ? 'bg-blue-100 text-blue-800' :
                        constitution.status === 'avant_projet' ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {constitution.status === 'active' ? 'Actif' :
                         constitution.status === 'draft' ? 'Brouillon' :
                         constitution.status === 'archived' ? 'Archivé' :
                         constitution.status === 'in_development' ? 'En projet' :
                         constitution.status === 'avant_projet' ? 'Avant Projet' :
                         constitution.status || 'Non spécifié'}
                      </span>
                    </p>
                  </div>
                  
                  <div className="text-xs sm:text-sm text-gray-500 break-words">
                    <span className="font-medium">Fichier:</span> {constitution.filename}
                  </div>
                </div>

                {/* Boutons toujours alignés en bas */}
                <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row gap-2 sm:space-x-2 pt-3 sm:pt-4 border-t border-gray-100">
                  <button 
                    onClick={() => navigate(`/pdf/${encodeURIComponent(constitution.filename)}`, { state: { title: constitution.title } })}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-xs sm:text-sm flex items-center justify-center space-x-1 transition-colors"
                  >
                    <EyeIcon className="h-3 w-3 sm:h-4 sm:w-4" />
                    <span>Voir</span>
                  </button>
                  <button 
                    onClick={async () => {
                      const url = `/api/constitutions/files/${encodeURIComponent(constitution.filename)}`;
                      const safeName = constitution.filename.endsWith('.pdf') ? constitution.filename : `${constitution.filename}.pdf`;
                      try {
                        await downloadFileFromUrl(url, safeName);
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-xs sm:text-sm flex items-center justify-center space-x-1 transition-colors"
                  >
                    <ArrowDownTrayIcon className="h-3 w-3 sm:h-4 sm:w-4" />
                    <span>Télécharger</span>
                  </button>
                </div>
              </div>
            ))
          )}
          </div>
      </div>

      {/* Modal d'upload amélioré */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900">Ajouter un fichier PDF</h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Zone de drop */}
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors relative ${
                  dragActive 
                    ? 'border-blue-400 bg-blue-50' 
                    : selectedFile
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-300 hover:border-blue-400'
                }`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                  const files = e.dataTransfer.files;
                  if (files.length > 0) {
                    const file = files[0];
                    if (file.type === 'application/pdf') {
                      // Traiter le fichier directement
                      handleFileUploadFromDrop(file);
                    } else {
                      showWarning('Type de fichier invalide', 'Veuillez sélectionner un fichier PDF.');
                    }
                  }
                }}
              >
                {selectedFile ? (
                  <div className="space-y-4">
                    <DocumentTextIcon className="mx-auto h-12 w-12 text-green-500" />
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-gray-900">
                        Fichier sélectionné
                      </p>
                      <p className="text-sm text-gray-600">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Changer de fichier
                    </button>
                  </div>
                ) : (
                  <>
                    <DocumentTextIcon className={`mx-auto h-12 w-12 mb-4 ${
                      dragActive ? 'text-blue-400' : 'text-gray-400'
                    }`} />
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-gray-900">
                        {dragActive ? 'Déposez le fichier ici' : 'Glissez-déposez votre fichier PDF ici'}
                      </p>
                      <p className="text-sm text-gray-500">
                        ou cliquez pour sélectionner un fichier
                      </p>
                      <p className="text-xs text-gray-400">
                        Taille maximale : 16MB
                      </p>
                    </div>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>

              {/* Barre de progression */}
              {uploading && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Upload en cours...</span>
                    <span className="text-sm text-gray-500">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Instructions */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Instructions :</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Seuls les fichiers PDF sont acceptés</li>
                  <li>• Taille maximale : 16MB</li>
                  <li>• Le fichier sera automatiquement analysé après l'upload</li>
                  <li>• Vous pourrez ensuite poser des questions à l'IA sur le document</li>
                </ul>
              </div>

              {/* Boutons d'action */}
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setSelectedFile(null);
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
                >
                  Annuler
                </button>
                {!selectedFile && (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                  >
                    Sélectionner un fichier
                  </button>
                )}
                {selectedFile && (
                  <button
                    onClick={handleSaveFile}
                    disabled={uploading}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Sauvegarde en cours...</span>
                      </>
                    ) : (
                      <span>Sauvegarder</span>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de suppression */}
      {showDeleteModal && deletingConstitution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Confirmer la suppression</h3>
            <p className="text-gray-600 mb-4">
              Êtes-vous sûr de vouloir supprimer "{deletingConstitution.title}" ?
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingConstitution(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Annuler
              </button>
              <button
                onClick={() => handleDeleteConstitution(deletingConstitution)}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded"
              >
                {deleting ? 'Suppression...' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal d'édition */}
      {showEditModal && editingConstitution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Modifier la constitution</h3>
                          <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  handleEditConstitution({
                    title: formData.get('title') as string,
                    year: parseInt(formData.get('year') as string) || undefined,
                    status: formData.get('status') as string,
                  });
                }}
              >
            <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Titre
                  </label>
                  <input
                    type="text"
                    name="title"
                    defaultValue={editingConstitution.title}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Année
                  </label>
                  <input
                    type="number"
                    name="year"
                    defaultValue={editingConstitution.year}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Statut
                  </label>
                  <select
                    name="status"
                    defaultValue={editingConstitution.status || 'active'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="draft">Brouillon</option>
                    <option value="active">Actif</option>
                    <option value="archived">Archivé</option>
                    <option value="in_development">En projet</option>
                    <option value="avant_projet">Avant Projet</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end space-x-2 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingConstitution(null);
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                >
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default ConstitutionsPage; 