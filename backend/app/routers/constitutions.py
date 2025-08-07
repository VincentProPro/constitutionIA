from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from app.database import get_db
from app.schemas.constitution import Constitution, ConstitutionCreate, ConstitutionUpdate, ConstitutionSearch
from app.models.constitution import Constitution as ConstitutionModel, ConstitutionStatus
from sqlalchemy import or_, and_
from app.services.pdf_analyzer import PDFAnalyzer
from app.services.file_watcher import FileWatcher
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[Constitution])
async def get_constitutions(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    status: Optional[ConstitutionStatus] = None,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les constitutions avec filtres optionnels"""
    query = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True)
    
    if year:
        query = query.filter(ConstitutionModel.year == year)
    if status:
        query = query.filter(ConstitutionModel.status == status)
    
    constitutions = query.offset(skip).limit(limit).all()
    return constitutions

@router.get("/years", response_model=List[int])
async def get_constitution_years(db: Session = Depends(get_db)):
    """Récupérer toutes les années disponibles"""
    years = db.query(ConstitutionModel.year).distinct().all()
    return [year[0] for year in years]

@router.get("/{constitution_id}", response_model=Constitution)
async def get_constitution(constitution_id: int, db: Session = Depends(get_db)):
    """Récupérer une constitution par ID"""
    constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == True
    ).first()
    
    if not constitution:
        raise HTTPException(status_code=404, detail="Constitution non trouvée")
    
    return constitution

@router.post("/", response_model=Constitution)
async def create_constitution(
    constitution: ConstitutionCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle constitution"""
    db_constitution = ConstitutionModel(**constitution.dict())
    db.add(db_constitution)
    db.commit()
    db.refresh(db_constitution)
    return db_constitution

@router.put("/{constitution_id}", response_model=Constitution)
async def update_constitution(
    constitution_id: int,
    constitution: ConstitutionUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une constitution"""
    db_constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == True
    ).first()
    
    if not db_constitution:
        raise HTTPException(status_code=404, detail="Constitution non trouvée")
    
    update_data = constitution.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_constitution, field, value)
    
    db.commit()
    db.refresh(db_constitution)
    return db_constitution

@router.delete("/{constitution_id}")
async def delete_constitution(constitution_id: int, db: Session = Depends(get_db)):
    """Supprimer une constitution (soft delete)"""
    db_constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == True
    ).first()
    
    if not db_constitution:
        raise HTTPException(status_code=404, detail="Constitution non trouvée")
    
    db_constitution.is_active = False
    db.commit()
    return {"message": "Constitution supprimée avec succès"}

@router.post("/search", response_model=List[Constitution])
async def search_constitutions(
    search: ConstitutionSearch,
    db: Session = Depends(get_db)
):
    """Rechercher des constitutions par contenu"""
    query = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True)
    
    # Recherche textuelle dans le titre et le contenu
    if search.query:
        search_term = f"%{search.query}%"
        query = query.filter(
            or_(
                ConstitutionModel.title.ilike(search_term),
                ConstitutionModel.content.ilike(search_term),
                ConstitutionModel.summary.ilike(search_term)
            )
        )
    
    # Filtres additionnels
    if search.year:
        query = query.filter(ConstitutionModel.year == search.year)
    if search.status:
        query = query.filter(ConstitutionModel.status == search.status)
    
    constitutions = query.offset(search.offset).limit(search.limit).all()
    return constitutions

@router.get("/files/list")
async def list_constitution_files():
    """Lister tous les fichiers PDF de constitutions disponibles"""
    files_dir = Path("Fichier")
    pdf_files = []
    
    if files_dir.exists():
        for file in files_dir.glob("*.pdf"):
            # Extraire l'année du nom de fichier si possible
            filename = file.stem
            year = None
            
            # Essayer d'extraire l'année du nom de fichier
            import re
            year_match = re.search(r'(\d{4})', filename)
            if year_match:
                year = int(year_match.group(1))
            
            pdf_files.append({
                "filename": file.name,
                "title": filename.replace("_", " ").title(),
                "year": year,
                "size": file.stat().st_size,
                "path": str(file)
            })
    
    # Trier par année (si disponible) puis par nom
    pdf_files.sort(key=lambda x: (x["year"] or 0, x["filename"]))
    return pdf_files

@router.get("/files/{filename}")
async def get_constitution_file(filename: str):
    """Télécharger un fichier PDF de constitution"""
    file_path = Path("Fichier") / filename
    
    if not file_path.exists() or not filename.endswith('.pdf'):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    from fastapi.responses import Response
    from fastapi import Response as FastAPIResponse
    
    # Lire le fichier
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Créer une réponse avec les headers CORS appropriés
    response = Response(
        content=content,
        media_type='application/pdf',
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f"inline; filename={filename}"
        }
    )
    
    return response

@router.head("/files/{filename}")
async def head_constitution_file(filename: str):
    """Gérer les requêtes HEAD pour CORS"""
    file_path = Path("Fichier") / filename
    
    if not file_path.exists() or not filename.endswith('.pdf'):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    from fastapi.responses import Response
    
    # Retourner une réponse HEAD avec les headers CORS
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Type": "application/pdf",
            "Content-Disposition": f"inline; filename={filename}"
        }
    )

@router.post("/analyze-files")
async def analyze_new_files(db: Session = Depends(get_db)):
    """Déclenche l'analyse des fichiers PDF"""
    try:
        print("Début de l'analyse des fichiers")
        
        # Initialiser l'analyseur PDF
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY non configurée")
        
        print("OpenAI API Key configurée")
        
        pdf_analyzer = PDFAnalyzer(openai_api_key)
        file_watcher = FileWatcher(pdf_analyzer)
        
        print("FileWatcher initialisé")
        
        # Traiter tous les fichiers PDF dans le dossier
        files_dir = Path("Fichier")
        processed_files = []
        
        if files_dir.exists():
            for pdf_file in files_dir.glob("*.pdf"):
                try:
                    print(f"Traitement du fichier: {pdf_file.name}")
                    constitution = file_watcher.force_reprocess_file(pdf_file.name, db)
                    if constitution:
                        processed_files.append(constitution)
                        print(f"Fichier retraité avec succès: {pdf_file.name}")
                except Exception as e:
                    print(f"Erreur lors du traitement de {pdf_file.name}: {e}")
        
        print(f"Fichiers traités: {len(processed_files)}")
        
        return {
            "message": f"{len(processed_files)} fichiers traités",
            "processed_files": [
                {
                    "filename": constitution.filename,
                    "title": constitution.title,
                    "year": constitution.year,
                    "status": constitution.status
                }
                for constitution in processed_files
            ]
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur détaillée lors de l'analyse: {error_details}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@router.post("/analyze-files/{filename}")
async def analyze_specific_file(filename: str, db: Session = Depends(get_db)):
    """Force l'analyse d'un fichier PDF spécifique"""
    try:
        # Vérifier que le fichier existe
        file_path = Path("Fichier") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Initialiser l'analyseur PDF
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY non configurée")
        
        pdf_analyzer = PDFAnalyzer(openai_api_key)
        file_watcher = FileWatcher(pdf_analyzer)
        
        # Forcer le retraitement du fichier
        constitution = file_watcher.force_reprocess_file(filename, db)
        
        if constitution:
            return {
                "message": f"Fichier {filename} retraité avec succès",
                "constitution": {
                    "filename": constitution.filename,
                    "title": constitution.title,
                    "year": constitution.year,
                    "status": constitution.status
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors du retraitement")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@router.get("/db/list", response_model=List[Constitution])
async def get_constitutions_from_db(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    status: Optional[ConstitutionStatus] = None,
    db: Session = Depends(get_db)
):
    """Récupérer les constitutions depuis la base de données"""
    query = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True)
    
    if year:
        query = query.filter(ConstitutionModel.year == year)
    if status:
        query = query.filter(ConstitutionModel.status == status)
    
    constitutions = query.offset(skip).limit(limit).all()
    return constitutions 

@router.delete("/files/{filename}")
async def delete_constitution_file(filename: str, db: Session = Depends(get_db)):
    """Supprimer un fichier de constitution"""
    try:
        # Vérifier que le fichier existe
        file_path = Path("Fichier") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Supprimer l'entrée de la base de données
        constitution = db.query(ConstitutionModel).filter(
            ConstitutionModel.filename == filename
        ).first()
        
        if constitution:
            db.delete(constitution)
            db.commit()
        
        # Supprimer le fichier physique
        file_path.unlink()
        
        return {
            "message": f"Fichier {filename} supprimé avec succès",
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@router.post("/upload")
async def upload_constitution_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploader un fichier PDF de constitution"""
    try:
        # Vérifier le type de fichier
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")
        
        # Vérifier la taille du fichier (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Le fichier est trop volumineux. Taille maximale : 10MB")
        
        # Créer le dossier Fichier s'il n'existe pas
        upload_dir = Path("Fichier")
        upload_dir.mkdir(exist_ok=True)
        
        # Générer un nom de fichier unique
        filename = file.filename
        file_path = upload_dir / filename
        
        # Vérifier si le fichier existe déjà
        counter = 1
        while file_path.exists():
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            file_path = upload_dir / filename
            counter += 1
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Créer une entrée simple dans la base de données
        new_constitution = ConstitutionModel(
            filename=filename,
            title=filename.replace('.pdf', ''),
            description='',
            year=None,
            country="Guinée",
            status=ConstitutionStatus.ACTIVE,
            content='',
            summary='',
            key_topics='',
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            is_active=True
        )
        
        db.add(new_constitution)
        db.commit()
        db.refresh(new_constitution)
        
        return {
            "message": f"Fichier {filename} uploadé et analysé avec succès",
            "filename": filename,
            "constitution": new_constitution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}") 