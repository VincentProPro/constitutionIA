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
  PencilIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import { useNotificationContext } from '../contexts/NotificationContext';
import Header from '../components/Header.js';
import Footer from '../components/Footer.js';

interface Constitution {
  id: number;
  title: string;
  year?: number;
  filename: string;
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
      const response = await axios.get('http://localhost:8000/api/constitutions/db/list');
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
      const response = await axios.post('http://localhost:8000/api/constitutions/analyze-files');
      showSuccess('Analyse terminée', 'Les fichiers ont été analysés avec succès.');
      await fetchConstitutions(); // Recharger les constitutions
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error);
      showError('Erreur d\'analyse', 'Une erreur est survenue lors de l\'analyse des fichiers.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showWarning('Type de fichier invalide', 'Veuillez sélectionner un fichier PDF.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/api/constitutions/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
      });

      showSuccess('Fichier uploadé', 'Le fichier a été uploadé avec succès.');
      setShowUploadModal(false);
      await fetchConstitutions();
    } catch (error) {
      console.error('Erreur lors de l\'upload:', error);
      showError('Erreur d\'upload', 'Une erreur est survenue lors de l\'upload du fichier.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteConstitution = async (constitution: Constitution) => {
    setDeleting(true);
    try {
      await axios.delete(`http://localhost:8000/api/constitutions/${constitution.id}`);
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
      await axios.put(`http://localhost:8000/api/constitutions/${editingConstitution.id}`, updatedConstitution);
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
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
                Constitutions de la Guinée
              </h1>
          <div className="flex space-x-4">
              <button
              onClick={handleAnalyzeFiles}
              disabled={analyzing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              {analyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Analyse en cours...</span>
                </>
              ) : (
                <>
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>Analyser les fichiers</span>
                </>
              )}
              </button>
              <button
              onClick={() => setShowUploadModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
              >
              <PlusIcon className="h-5 w-5" />
              <span>Ajouter un fichier PDF</span>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredConstitutions.length === 0 ? (
            <div className="col-span-full text-center py-8">
              <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucune constitution trouvée</p>
            </div>
          ) : (
            filteredConstitutions.map((constitution) => (
              <div key={constitution.id} className="bg-white rounded-lg shadow-md p-6 flex flex-col h-64">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-gray-900 flex-1 pr-2">
                    {constitution.title}
                  </h3>
                  <div className="flex space-x-2 flex-shrink-0">
                    <button
                      onClick={() => {
                        setEditingConstitution(constitution);
                        setShowEditModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
            <button
              onClick={() => {
                        setDeletingConstitution(constitution);
                        setShowDeleteModal(true);
              }}
                      className="text-red-600 hover:text-red-800"
            >
                      <TrashIcon className="h-5 w-5" />
            </button>
                  </div>
                </div>

                <div className="space-y-2 flex-1">
                  <p className="text-gray-600">
                    <span className="font-medium">Année:</span> {constitution.year || 'Non spécifiée'}
                </p>
                  <p className="text-sm text-gray-500">
                    <span className="font-medium">Fichier:</span> {constitution.filename}
                  </p>
                </div>

                <div className="mt-4 flex space-x-2">
                  <button 
                    onClick={() => navigate(`/pdf/${encodeURIComponent(constitution.filename)}`)}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm flex items-center justify-center space-x-1"
                  >
                    <EyeIcon className="h-4 w-4" />
                    <span>Voir</span>
                  </button>
                  <button 
                    onClick={() => {
                      // Télécharger le fichier
                      const link = document.createElement('a');
                      link.href = `http://localhost:8000/api/constitutions/download/${encodeURIComponent(constitution.filename)}`;
                      link.download = constitution.filename;
                      link.click();
                    }}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm flex items-center justify-center space-x-1"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4" />
                    <span>Télécharger</span>
                  </button>
                </div>
              </div>
            ))
          )}
          </div>
      </div>

      {/* Modal d'upload */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Ajouter un fichier PDF</h3>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
              className="w-full mb-4"
            />
              {uploading && (
              <div className="mb-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                    className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                <p className="text-sm text-gray-600 mt-1">{uploadProgress}%</p>
                </div>
              )}
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Annuler
              </button>
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