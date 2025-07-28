import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  PlayIcon,
  DocumentTextIcon,
  LightBulbIcon,
  UserGroupIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import Footer from '../components/Footer.js';
import Header from '../components/Header.js';

const HomePage: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isHeaderVisible, setIsHeaderVisible] = useState(false);

  // Gestion du scroll pour afficher/masquer le header
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const sliderHeight = window.innerHeight; // Hauteur du slider
      
      // Afficher le header quand on dépasse la hauteur du slider
      if (scrollPosition > sliderHeight * 0.8) {
        setIsHeaderVisible(true);
      } else {
        setIsHeaderVisible(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Données du slider avec des images locales
  const sliderData = [
    {
      id: 1,
      title: "ConstitutionIA",
      subtitle: "Plateforme de gestion des constitutions",
      description: "Accédez facilement aux constitutions de la Guinée et interrogez notre assistant IA",
      image: "/images/slider/slide-1.jpg",
      cta: "Explorer les Constitutions"
    },
    {
      id: 2,
      title: "Copilot IA",
      subtitle: "Assistant intelligent",
      description: "Posez vos questions à notre IA spécialisée dans les constitutions",
      image: "/images/slider/slide-2.jpg",
      cta: "Tester le Copilot"
    },
    {
      id: 3,
      title: "Recherche Avancée",
      subtitle: "Trouvez rapidement",
      description: "Recherchez dans le contenu des constitutions avec des filtres précis",
      image: "/images/slider/slide-3.jpg",
      cta: "Rechercher"
    }
  ];

  // Auto-play slider
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % sliderData.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [sliderData.length]);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % sliderData.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + sliderData.length) % sliderData.length);
  };

  return (
    <div className="min-h-screen">
      {/* Header avec effet de scroll */}
      <div 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isHeaderVisible 
            ? 'transform translate-y-0 opacity-100' 
            : 'transform -translate-y-full opacity-0'
        }`}
      >
        <Header />
      </div>

      {/* Slider Section */}
      <section className="relative h-screen overflow-hidden">
        {sliderData.map((slide, index) => (
          <div
            key={slide.id}
            className={`absolute inset-0 transition-opacity duration-1000 ${
              index === currentSlide ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <div 
              className="absolute inset-0 bg-cover bg-center"
              style={{ backgroundImage: `url(${slide.image})` }}
            >
              <div className="absolute inset-0 bg-black bg-opacity-50"></div>
            </div>
            <div className="relative h-full flex items-center justify-center">
              <div className="text-center text-white max-w-4xl mx-auto px-4">
                <h1 className="text-5xl md:text-7xl font-bold mb-4">
                  {slide.title}
                </h1>
                <h2 className="text-2xl md:text-3xl font-semibold mb-4 text-blue-200">
                  {slide.subtitle}
                </h2>
                <p className="text-lg md:text-xl mb-8 text-gray-200">
                  {slide.description}
                </p>
                <Link
                  to={slide.cta.includes("Copilot") ? "/ai-copilot" : "/constitutions"}
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors duration-200"
                >
                  {slide.cta}
                </Link>
              </div>
            </div>
          </div>
        ))}

        {/* Navigation arrows */}
        <button
          onClick={prevSlide}
          className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-2 rounded-full transition-all duration-200"
        >
          <ChevronLeftIcon className="w-6 h-6" />
        </button>
        <button
          onClick={nextSlide}
          className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-2 rounded-full transition-all duration-200"
        >
          <ChevronRightIcon className="w-6 h-6" />
        </button>

        {/* Dots indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-2">
          {sliderData.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentSlide(index)}
              className={`w-3 h-3 rounded-full transition-all duration-200 ${
                index === currentSlide ? 'bg-white' : 'bg-white bg-opacity-50'
              }`}
            />
          ))}
        </div>
      </section>

      {/* TEST SECTION - À propos de nous */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                À propos de nous
              </h2>
              <div className="w-24 h-1 bg-blue-600 mb-6"></div>
              
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                ConstitutionIA est une plateforme innovante dédiée à la démocratisation de l'accès 
                aux constitutions de la Guinée.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/constitutions"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200 text-center"
                >
                  Explorer les Constitutions
                </Link>
              </div>
            </div>
            
            <div className="relative">
              <div className="rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="/images/about-1.jpg"
                  alt="À propos de ConstitutionIA"
                  className="w-full h-auto object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Vision Simandou 2040 Section */}
      <section className="py-16 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="relative">
              <div className="rounded-2xl overflow-hidden shadow-2xl bg-white p-6">
                <img
                  src="/images/simandouguinea.png"
                  alt="Vision Simandou 2040"
                  className="w-full h-auto object-contain"
                />
                <div className="text-center mt-4">
                  <p className="text-sm text-gray-600 font-medium">
                    Simandou Guinée - Vision 2040
                  </p>
                </div>
              </div>
            </div>
            
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Vision Simandou 2040
              </h2>
              <div className="w-24 h-1 bg-blue-600 mb-6"></div>
              
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                ConstitutionIA s'inscrit dans la vision ambitieuse de la Guinée pour 2040, 
                portée par le projet Simandou. Notre plateforme contribue à cette transformation 
                en démocratisant l'accès aux informations constitutionnelles et en favorisant 
                la transparence démocratique.
              </p>
              
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                À travers l'intelligence artificielle et l'innovation technologique, 
                nous participons à la modernisation de l'État guinéen et à l'émergence 
                d'une société numérique inclusive, alignée sur les objectifs de développement 
                durable de la Vision Simandou 2040.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/ai-copilot"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200 text-center"
                >
                  Discuter avec l'IA
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mot du Directeur Général Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
                          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Mot du Directeur Général
              </h2>
              <div className="w-24 h-1 bg-blue-600 mx-auto"></div>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row items-center mb-8">
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-full overflow-hidden shadow-lg mb-6 md:mb-0 md:mr-8">
                  <img
                    src="/images/dg.jpg"
                    alt="Directeur Général"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="text-center md:text-left">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Mamadou Diallo</h3>
                  <p className="text-blue-600 font-semibold text-lg">Directeur Général</p>
                  <p className="text-gray-600 mt-2">ConstitutionIA</p>
                </div>
              </div>
              
              <div className="prose prose-lg max-w-none">
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  "Chers citoyens, chers utilisateurs,
                </p>
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  ConstitutionIA représente une étape majeure dans notre engagement en faveur de la 
                  transparence et de l'accessibilité des informations constitutionnelles. Cette plateforme 
                  innovante témoigne de notre volonté de moderniser l'accès aux documents fondamentaux 
                  de notre République.
                </p>
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  Notre mission est de rendre les constitutions plus compréhensibles et accessibles 
                  à tous les Guinéens. Grâce à l'intelligence artificielle, nous offrons un outil 
                  puissant qui facilite la recherche et l'analyse des textes constitutionnels.
                </p>
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  Je vous invite à explorer cette plateforme et à découvrir les nouvelles possibilités 
                  qu'elle offre pour mieux comprendre notre cadre constitutionnel.
                </p>
                <p className="text-lg text-gray-700 mt-8 font-semibold">
                  Ensemble, construisons une Guinée plus transparente et démocratique."
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default HomePage; 