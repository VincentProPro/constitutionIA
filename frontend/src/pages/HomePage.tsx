import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChevronLeftIcon, 
  ChevronRightIcon
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
      image: "/images/slider/slide-7.jpg",
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
      id: 2,
      title: "OUI",
      subtitle: "À LA NOUVELLE CONSTITUTION",
      description: "Découvrez la nouvelle Constitution guinéenne",
      image: "/images/slider/slide-5.jpg",
      cta: "Tester le Copilot"
    },
  
    {
      id: 4,
      title: "Analyse Intelligente",
      subtitle: "Compréhension approfondie",
      description: "Analysez les constitutions avec des outils d'IA avancés pour une meilleure compréhension",
      image: "/images/slider/slide-4.jpg",
      cta: "Analyser"
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
              className="absolute inset-0 bg-cover bg-center bg-no-repeat"
              style={{ 
                backgroundImage: `url(${slide.image})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat'
              }}
            >
              <div className="absolute inset-0 bg-black bg-opacity-50"></div>
            </div>
            <div className="relative h-full flex items-center justify-center px-4">
              <div className="text-center text-white max-w-4xl mx-auto">
                <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-bold mb-2 md:mb-4">
                  {slide.title}
                </h1>
                <h2 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-semibold mb-2 md:mb-4 text-blue-200">
                  {slide.subtitle}
                </h2>
                <p className="text-sm sm:text-base md:text-lg lg:text-xl mb-4 md:mb-8 text-gray-200 leading-relaxed">
                  {slide.description}
                </p>
                <Link
                  to={slide.cta.includes("Copilot") ? "/ai-copilot" : "/constitutions"}
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 sm:px-6 md:px-8 py-2 sm:py-3 rounded-lg font-semibold transition-colors duration-200 text-sm sm:text-base"
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
          className="absolute left-2 sm:left-4 top-1/2 transform -translate-y-1/2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-1 sm:p-2 rounded-full transition-all duration-200 z-10"
        >
          <ChevronLeftIcon className="w-4 h-4 sm:w-6 sm:h-6" />
        </button>
        <button
          onClick={nextSlide}
          className="absolute right-2 sm:right-4 top-1/2 transform -translate-y-1/2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-1 sm:p-2 rounded-full transition-all duration-200 z-10"
        >
          <ChevronRightIcon className="w-4 h-4 sm:w-6 sm:h-6" />
        </button>

        {/* Dots indicator */}
        <div className="absolute bottom-4 sm:bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-1 sm:space-x-2 z-10">
          {sliderData.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentSlide(index)}
              className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-200 ${
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
                ConstitutionIA est une plateforme intelligente conçue pour faciliter la compréhension et la vulgarisation de la Constitution guinéenne, en la rendant accessible, claire et interactive pour tous les citoyens.
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
              ConstitutionIA est une IA conçue pour rendre la Constitution guinéenne compréhensible et accessible à tous, en facilitant l’accès aux droits et devoirs citoyens.              
              </p>
              
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
              Elle s’inscrit dans la vision Simandou 2040 en promouvant une gouvernance inclusive, la transparence et une participation citoyenne active au service d’un développement durable.              </p>
              
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

      {/* Mot du Président Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
                          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Mot du Président
              </h2>
              <div className="w-24 h-1 bg-blue-600 mx-auto"></div>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row items-center mb-8">
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-full overflow-hidden shadow-lg mb-6 md:mb-0 md:mr-8">
                  <img
                    src="/images/Dr-Dansa-Kourouma.jpg"
                    alt="Président"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="text-center md:text-left">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Dr Dansa KOUROUMA</h3>
                  <p className="text-blue-600 font-semibold text-lg">Président</p>
                  <p className="text-gray-600 mt-2">Conseil National de la Transition GN</p>
                </div>
              </div>
              
              <div className="prose prose-lg max-w-none">
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  "Chers citoyens, chers utilisateurs,
                </p>
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                ConstitutionIA marque une avancée majeure vers une citoyenneté éclairée et active. En rendant notre Loi fondamentale accessible à tous, elle concrétise notre vision d’une Guinée plus juste, inclusive et tournée vers l’avenir. 
               
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