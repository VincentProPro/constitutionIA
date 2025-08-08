import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gradient-to-b from-gray-900 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo et description */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-white">ConstitutionIA</span>
            </div>
            <p className="text-gray-300 mb-4">
              Plateforme de gestion des constitutions avec copilot IA pour faciliter 
              la recherche et l'analyse des documents constitutionnels.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white">
                <span className="sr-only">Facebook</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-white">
                <span className="sr-only">Twitter</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                </svg>
              </a>
            </div>
            <div className="mt-2">
              <img 
                src="/images/simandouguinea2.png" 
                alt="Simandou Guinée" 
                className="h-20 w-auto opacity-90 hover:opacity-100 transition-opacity"
              />
            </div>
          </div>

          {/* Liens rapides */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase mb-4">
              Navigation
            </h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-gray-300 hover:text-white">
                  Accueil
                </Link>
              </li>
              <li>
                <Link to="/constitutions" className="text-gray-300 hover:text-white">
                  Constitutions
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase mb-4">
              Contact
            </h3>
            <ul className="space-y-2">
              <li className="text-gray-300">
                <span className="block">Email:</span>
                <a href="mailto:contact@constitutionia.gn" className="hover:text-white">
                  contact@constitutionia.gn
                </a>
              </li>
              <li className="text-gray-300">
                <span className="block">Téléphone:</span>
                <a href="tel:+224123456789" className="hover:text-white">
                  +224 123 456 789
                </a>
              </li>
              <li className="text-gray-300">
                <span className="block">Adresse:</span>
                <span>Conakry, Guinée</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Section blanche avec l'image */}
        <div 
          className="mt-10 pt-8 border-t border-gray-300 bg-white rounded-lg p-4" 
          style={{
            paddingTop: '0px',
            paddingBottom: '0px'
          }}
        >
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-600 text-sm">
              © 2025 ANDE. Tous droits réservés.
            </p>
            <div className="flex items-center mt-4 md:mt-0">
              <img 
                src="/images/ANDE_TRANS.png" 
                alt="ANDE" 
                className="h-20 w-auto opacity-90 hover:opacity-100 transition-opacity"
              />
            </div>
            <div className="flex items-center mt-4 md:mt-0">
              <img 
                src="/images/ministre.webp" 
                alt="ministere" 
                className="h-20 w-auto opacity-90 hover:opacity-100 transition-opacity"
              />
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 