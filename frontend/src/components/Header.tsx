import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Bars3Icon, 
  XMarkIcon, 
  MagnifyingGlassIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';

interface Constitution {
  id: number;
  title: string;
  year: number;
  filename: string;
}

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [constitutions, setConstitutions] = useState<Constitution[]>([]);
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  // Récupérer les constitutions depuis l'API
  useEffect(() => {
    const fetchConstitutions = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:8000/api/constitutions/db/list');
        if (response.ok) {
          const data = await response.json();
          setConstitutions(data);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des constitutions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConstitutions();
  }, []);

  // Grouper les constitutions par année
  const constitutionsByYear = constitutions.reduce((acc, constitution) => {
    const year = constitution.year || 0;
    if (!acc[year]) {
      acc[year] = [];
    }
    acc[year].push(constitution);
    return acc;
  }, {} as Record<number, Constitution[]>);

  // Trier les années par ordre décroissant
  const sortedYears = Object.keys(constitutionsByYear)
    .map(Number)
    .sort((a, b) => b - a);

  const navigation = [
    { name: 'Accueil', href: '/' },
    { name: 'Copilot IA', href: '/ai-copilot' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-gray-900">ConstitutionIA</span>
            </Link>
          </div>

          {/* Navigation Desktop */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive(item.href)
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                }`}
              >
                {item.name}
              </Link>
            ))}
            
            {/* Menu Constitutions avec sous-menus */}
            <div className="relative constitutions-dropdown group">
              <Link
                to="/constitutions"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center space-x-1 ${
                  location.pathname.startsWith('/constitutions') || location.pathname.startsWith('/pdf/')
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                }`}
              >
                <span>Constitutions</span>
                <ChevronDownIcon className="h-4 w-4 transition-transform duration-200 group-hover:rotate-180" />
              </Link>

              {/* Dropdown Menu - visible au hover */}
              <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                <div className="py-2">
                  {loading ? (
                    <div className="px-4 py-2 text-sm text-gray-500">
                      Chargement...
                    </div>
                  ) : sortedYears.length > 0 ? (
                    sortedYears.map((year) => (
                      <div key={year} className="border-b border-gray-100 last:border-b-0">
                        <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                          Constitution {year}
                        </div>
                        {constitutionsByYear[year].map((constitution) => (
                          <Link
                            key={constitution.id}
                            to={`/pdf/${encodeURIComponent(constitution.filename)}`}
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-600"
                          >
                            {constitution.title}
                          </Link>
                        ))}
                      </div>
                    ))
                  ) : (
                    <div className="px-4 py-2 text-sm text-gray-500">
                      Aucune constitution disponible
                    </div>
                  )}
                </div>
              </div>
            </div>
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-4">
            {/* Search */}
            <button className="p-2 text-gray-400 hover:text-gray-500">
              <MagnifyingGlassIcon className="h-5 w-5" />
            </button>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-gray-400 hover:text-gray-500"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`block px-3 py-2 rounded-md text-base font-medium ${
                    isActive(item.href)
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                  }`}
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
              
              {/* Menu Constitutions Mobile */}
              <div className="border-t border-gray-200 pt-2 mt-2">
                <div className="px-3 py-2 text-sm font-semibold text-gray-500 uppercase tracking-wide">
                  Constitutions
                </div>
                {loading ? (
                  <div className="px-3 py-2 text-sm text-gray-500">
                    Chargement...
                  </div>
                ) : sortedYears.length > 0 ? (
                  sortedYears.map((year) => (
                    <div key={year}>
                      <div className="px-3 py-1 text-xs font-semibold text-gray-400">
                        Constitution {year}
                      </div>
                      {constitutionsByYear[year].map((constitution) => (
                        <Link
                          key={constitution.id}
                          to={`/pdf/${encodeURIComponent(constitution.filename)}`}
                          className="block px-6 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-600"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          {constitution.title}
                        </Link>
                      ))}
                    </div>
                  ))
                ) : (
                  <div className="px-3 py-2 text-sm text-gray-500">
                    Aucune constitution disponible
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header; 