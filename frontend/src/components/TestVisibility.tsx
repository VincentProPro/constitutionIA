import React from 'react';

const TestVisibility: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Test de Visibilité</h1>
      
      <div className="space-y-4">
        <div className="bg-red-100 p-4 rounded">
          <h2 className="font-semibold text-red-800">Header Test</h2>
          <p className="text-red-600">Si vous voyez ce texte, le header est visible</p>
        </div>
        
        <div className="bg-blue-100 p-4 rounded">
          <h2 className="font-semibold text-blue-800">Contenu Principal</h2>
          <p className="text-blue-600">Ceci est le contenu principal de la page</p>
        </div>
        
        <div className="bg-green-100 p-4 rounded">
          <h2 className="font-semibold text-green-800">Footer Test</h2>
          <p className="text-green-600">Si vous voyez ce texte, le footer est visible</p>
        </div>
      </div>
      
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-2">Instructions de test :</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-700">
          <li>Le header doit être visible en haut de la page</li>
          <li>Le footer doit être visible en bas de la page</li>
          <li>Le contenu principal doit être entre les deux</li>
          <li>Le header doit rester fixe lors du défilement</li>
        </ul>
      </div>
    </div>
  );
};

export default TestVisibility; 