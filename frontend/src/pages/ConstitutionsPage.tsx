import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  DocumentTextIcon,
  CalendarIcon,
  EyeIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import Footer from '../components/Footer.js';
import Header from '../components/Header.js';

interface Constitution {
  id: number;
  filename: string;
  title: string;
  description: string;
  year: number | null;
  country: string;
  status: string;
  summary: string | null;
  file_size: number;
  file_path: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

const ConstitutionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [constitutions, setConstitutions] = useState<Constitution[]>([]);
  const [filteredConstitutions, setFilteredConstitutions] = useState<Constitution[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [years, setYears] = useState<number[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchConstitutions();
    fetchYears();
  }, []);

  useEffect(() => {
    filterConstitutions();
  }, [constitutions, searchQuery, selectedYear]);

  const fetchConstitutions = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/constitutions/db/list');
      setConstitutions(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erreur lors du chargement des constitutions:', error);
      setLoading(false);
    }
  };

  const fetchYears = async () => {
    try {
      // Extraire les années uniques depuis la base de données
      const response = await axios.get('http://localhost:8000/api/constitutions/db/list');
      const files = response.data;
      const uniqueYears = [...new Set(files.map((file: Constitution) => file.year).filter((year): year is number => year !== null))] as number[];
      setYears(uniqueYears.sort());
    } catch (error) {
      console.error('Erreur lors du chargement des années:', error);
    }
  };

  const filterConstitutions = () => {
    let filtered = constitutions;

    // Filtre par recherche textuelle
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



  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement des constitutions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Constitutions de la Guinée
              </h1>
              <p className="text-lg text-gray-600 max-w-3xl">
                Explorez et recherchez dans les constitutions de la Guinée. Utilisez les filtres pour trouver 
                rapidement les documents par année, statut ou contenu.
              </p>
            </div>
            <button
              onClick={async () => {
                console.log('Bouton "Analyser les fichiers" cliqué');
                try {
                  console.log('Envoi de la requête POST à /api/constitutions/analyze-files');
                  const response = await axios.post('http://localhost:8000/api/constitutions/analyze-files');
                  console.log('Réponse reçue:', response.data);
                  alert(`Analyse des fichiers terminée ! ${response.data.message}`);
                  fetchConstitutions(); // Recharger les données
                } catch (error) {
                  console.error('Erreur lors de l\'analyse:', error);
                  console.error('Détails de l\'erreur:', error.response?.data);
                  alert(`Erreur lors de l'analyse des fichiers: ${error.response?.data?.detail || error.message}`);
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Analyser les fichiers
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="card mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher dans les constitutions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn-secondary flex items-center space-x-2"
            >
              <FunnelIcon className="h-5 w-5" />
              <span>Filtres</span>
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Year Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Année
                  </label>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    className="input-field"
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

        {/* Results */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <p className="text-gray-600">
                <span className="font-semibold text-gray-900">{filteredConstitutions.length}</span> 
                constitution{filteredConstitutions.length > 1 ? 's' : ''} trouvée{filteredConstitutions.length > 1 ? 's' : ''}
              </p>
              {(searchQuery || selectedYear) && (
                <span className="text-sm text-gray-500">
                  (sur {constitutions.length} total)
                </span>
              )}
            </div>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedYear('');
              }}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium hover:underline"
            >
              Réinitialiser les filtres
            </button>
          </div>
        </div>

        {/* Constitutions Grid */}
        {filteredConstitutions.length === 0 ? (
          <div className="card text-center py-12">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Aucune constitution trouvée
            </h3>
            <p className="text-gray-600">
              Essayez de modifier vos critères de recherche
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredConstitutions.map((constitution) => (
              <div key={constitution.filename} className="card hover:shadow-lg transition-all duration-200 hover:scale-105">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700 bg-gray-100 px-2 py-1 rounded">
                      {constitution.year || 'N/A'}
                    </span>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    PDF
                  </span>
                </div>

                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {constitution.title}
                </h3>

                <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                  Fichier PDF de constitution
                </p>

                <div className="flex items-center justify-between text-sm text-gray-500 mb-6">
                  <div className="flex items-center space-x-1">
                    <CalendarIcon className="h-4 w-4" />
                    <span>
                      {(constitution.file_size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <span className="font-medium">Guinée</span>
                </div>

                <div className="flex space-x-3">
                  <button 
                    onClick={() => navigate(`/pdf/${encodeURIComponent(constitution.filename)}`)}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
                  >
                    <EyeIcon className="h-4 w-4" />
                    <span>Consulter</span>
                  </button>
                  <button 
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = `http://localhost:8000/api/constitutions/files/${constitution.filename}`;
                      link.download = constitution.filename;
                      link.click();
                    }}
                    className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4" />
                    <span>Télécharger</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default ConstitutionsPage; 