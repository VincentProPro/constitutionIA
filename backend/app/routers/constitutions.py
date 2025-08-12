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
from app.services.pdf_import import process_uploaded_pdf, delete_pdf_articles
from app.models.pdf_import import Article, Metadata
from app.core.config import settings

# Ajout pour Range support
from fastapi import Request
from starlette.responses import StreamingResponse

router = APIRouter()

@router.get("/", response_model=List[Constitution])
async def get_constitutions(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    status: Optional[ConstitutionStatus] = None,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les constitutions actives avec filtres optionnels"""
    query = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True)
    
    if year:
        query = query.filter(ConstitutionModel.year == year)
    if status:
        query = query.filter(ConstitutionModel.status == status)
    
    constitutions = query.offset(skip).limit(limit).all()
    return constitutions

@router.get("/all", response_model=List[Constitution])
async def get_all_constitutions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les constitutions (actives et inactives)"""
    query = db.query(ConstitutionModel)
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
    """Supprimer une constitution (soft delete) et nettoyer les articles"""
    db_constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == True
    ).first()
    
    if not db_constitution:
        raise HTTPException(status_code=404, detail="Constitution non trouvée")
    
    # Supprimer les articles associés
    articles_deleted = db.query(Article).filter(Article.constitution_id == constitution_id).delete()
    
    # Soft delete de la constitution
    db_constitution.is_active = False
    
    # Vérifier s'il reste des constitutions actives
    active_constitutions = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True).count()
    
    # Si aucune constitution active, réactiver la plus récente qui a des articles
    if active_constitutions == 0:
        # Trouver la constitution inactive la plus récente qui a des articles
        inactive_constitution = db.query(ConstitutionModel).filter(
            ConstitutionModel.is_active == False
        ).order_by(ConstitutionModel.created_at.desc()).first()
        
        if inactive_constitution:
            # Réactiver cette constitution et extraire ses articles
            inactive_constitution.is_active = True
            db.commit()
            
            # Réactiver cette constitution (les articles seront importés manuellement)
            return {
                "message": f"Constitution '{db_constitution.title}' supprimée. Constitution '{inactive_constitution.title}' réactivée automatiquement. Veuillez importer les articles manuellement.",
                "articles_deleted": articles_deleted,
                "constitution_reactivated": inactive_constitution.title,
                "note": "Importez les articles avec: python fix_articles_constitution_links.py"
            }
    
    db.commit()
    
    return {
        "message": f"Constitution '{db_constitution.title}' supprimée avec succès",
        "articles_deleted": articles_deleted
    }

@router.post("/{constitution_id}/reactivate")
async def reactivate_constitution(constitution_id: int, db: Session = Depends(get_db)):
    """Réactiver une constitution inactive et importer ses articles"""
    db_constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == False
    ).first()
    
    if not db_constitution:
        raise HTTPException(status_code=404, detail="Constitution inactive non trouvée")
    
    # Désactiver toutes les autres constitutions
    db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True).update({"is_active": False})
    
    # Réactiver cette constitution
    db_constitution.is_active = True
    db.commit()
    
    # Réactiver cette constitution (les articles seront importés manuellement)
    return {
        "message": f"Constitution '{db_constitution.title}' réactivée avec succès. Veuillez importer les articles manuellement.",
        "note": "Importez les articles avec: python fix_articles_constitution_links.py"
    }

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
async def get_constitution_file(filename: str, request: Request):
    """Télécharger un fichier PDF de constitution (supporte les requêtes Range)"""
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = Path(current_dir) / "Fichier" / filename
    
    if not file_path.exists() or not filename.endswith('.pdf'):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    file_size = file_path.stat().st_size

    # Gestion des requêtes Range
    range_header = request.headers.get('range') or request.headers.get('Range')
    if range_header and range_header.startswith('bytes='):
        # Exemple d'en-tête: Range: bytes=START-END
        range_spec = range_header.split('=')[1]
        start_str, end_str = (range_spec.split('-') + [''])[:2]
        try:
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except ValueError:
            start, end = 0, file_size - 1
        if start < 0:
            start = 0
        if end >= file_size:
            end = file_size - 1
        if start > end:
            start, end = 0, file_size - 1
        chunk_size = (end - start) + 1

        def iter_file(path: Path, offset: int, length: int, block_size: int = 1024 * 64):
            with open(path, 'rb') as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    read_size = block_size if remaining >= block_size else remaining
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        return StreamingResponse(
            iter_file(file_path, start, chunk_size),
            status_code=206,
            media_type='application/pdf',
            headers=headers
        )

    # Réponse normale (pas de Range)
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Accept-Ranges": "bytes"
        }
    )

@router.head("/files/{filename}")
async def head_constitution_file(filename: str):
    """Gérer les requêtes HEAD pour CORS"""
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = Path(current_dir) / "Fichier" / filename
    
    if not file_path.exists() or not filename.endswith('.pdf'):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    from fastapi.responses import Response
    
    # Lire la taille du fichier pour le Content-Length
    file_size = file_path.stat().st_size
    
    # Retourner une réponse HEAD avec les headers CORS et no-cache
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Type": "application/pdf",
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Length": str(file_size),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Accept-Ranges": "bytes"
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
            # Supprimer les articles associés
            try:
                delete_pdf_articles(db, constitution.id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Erreur lors de la suppression des articles: {e}")
            
            # Supprimer la constitution
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
        
        # Vérifier la taille du fichier (max 16MB)
        if file.size and file.size > 16 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Le fichier est trop volumineux. Taille maximale : 16MB")
        
        # Créer le dossier Fichier s'il n'existe pas
        upload_dir = Path("Fichier")
        upload_dir.mkdir(exist_ok=True)
        
        # Générer un nom de fichier UNIQUE systématiquement (base assainie + timestamp)
        import re
        from datetime import datetime
        original_name, ext = os.path.splitext(file.filename)
        safe_base = re.sub(r"[^A-Za-z0-9 _\.-]+", "", original_name).strip()
        if not safe_base:
            safe_base = "document"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{safe_base}-{timestamp}{ext}"
        file_path = upload_dir / filename
        
        # En cas de collision improbable, ajouter un compteur
        counter = 1
        while file_path.exists():
            filename = f"{safe_base}-{timestamp}_{counter}{ext}"
            file_path = upload_dir / filename
            counter += 1
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Créer une entrée simple dans la base de données
        new_constitution = ConstitutionModel(
            filename=filename,
            title=safe_base,
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
        
        # Traitement automatique du PDF pour extraire les articles
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            result = process_uploaded_pdf(db, new_constitution.id, str(file_path))
            if result['success']:
                logger.info(f"✅ Articles extraits: {result['articles_count']} articles trouvés")
                
                # Rafraîchir la base vectorielle avec les nouveaux articles
                try:
                    from app.services.optimized_ai_service import get_optimized_ai_service
                    ai_service = get_optimized_ai_service()
                    ai_service.refresh_vector_db()
                    logger.info("✅ Base vectorielle rafraîchie avec les nouveaux articles")
                except Exception as refresh_error:
                    logger.warning(f"⚠️ Échec du rafraîchissement de la base vectorielle: {refresh_error}")
                
                # Mettre à jour le message de retour
                message = f"Fichier {filename} uploadé et analysé avec succès ({result['articles_count']} articles extraits)"
            else:
                logger.warning(f"⚠️ Échec de l'extraction des articles: {result.get('error', 'Erreur inconnue')}")
                message = f"Fichier {filename} uploadé mais échec de l'extraction des articles"
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement automatique: {e}")
            message = f"Fichier {filename} uploadé mais erreur lors de l'analyse"
        
        return {
            "message": message,
            "filename": filename,
            "constitution": new_constitution,
            "articles_extracted": result.get('articles_count', 0) if 'result' in locals() else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@router.get("/{constitution_id}/articles")
async def get_constitution_articles(
    constitution_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer tous les articles d'une constitution"""
    try:
        # Vérifier que la constitution existe
        constitution = db.query(ConstitutionModel).filter(
            ConstitutionModel.id == constitution_id,
            ConstitutionModel.is_active == True
        ).first()
        
        if not constitution:
            raise HTTPException(status_code=404, detail="Constitution non trouvée")
        
        # Récupérer les articles
        articles = db.query(Article).filter(
            Article.constitution_id == constitution_id
        ).order_by(Article.article_number).all()
        
        # Formater la réponse
        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "article_number": article.article_number,
                "title": article.title,
                "content": article.content,
                "part": article.part,
                "section": article.section,
                "page_number": article.page_number,
                "created_at": article.created_at,
                "updated_at": article.updated_at
            })
        
        return {
            "constitution": {
                "id": constitution.id,
                "title": constitution.title,
                "filename": constitution.filename
            },
            "articles_count": len(articles_data),
            "articles": articles_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des articles: {str(e)}")

@router.get("/articles/search")
async def search_articles(
    query: str = Query(..., description="Terme de recherche"),
    constitution_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Rechercher dans les articles"""
    try:
        # Construire la requête
        search_query = db.query(Article).filter(
            or_(
                Article.content.ilike(f"%{query}%"),
                Article.article_number.ilike(f"%{query}%"),
                Article.title.ilike(f"%{query}%")
            )
        )
        
        # Filtrer par constitution si spécifié
        if constitution_id:
            search_query = search_query.filter(Article.constitution_id == constitution_id)
        
        # Récupérer les résultats
        articles = search_query.limit(50).all()
        
        # Formater la réponse
        results = []
        for article in articles:
            # Récupérer les informations de la constitution
            constitution = db.query(ConstitutionModel).filter(
                ConstitutionModel.id == article.constitution_id
            ).first()
            
            results.append({
                "id": article.id,
                "article_number": article.article_number,
                "title": article.title,
                "content": article.content[:200] + "..." if len(article.content) > 200 else article.content,
                "part": article.part,
                "section": article.section,
                "constitution": {
                    "id": constitution.id if constitution else None,
                    "title": constitution.title if constitution else "Inconnue",
                    "filename": constitution.filename if constitution else "Inconnu"
                }
            })
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}") 

@router.get("/automation/status")
async def get_automation_status():
    """Obtenir le statut du service d'automatisation"""
    from app.services.automation_service import get_automation_service
    service = get_automation_service()
    return service.get_status()

@router.post("/automation/force-process/{filename}")
async def force_process_file(filename: str):
    """Forcer le traitement d'un fichier spécifique"""
    try:
        from app.services.automation_service import get_automation_service
        service = get_automation_service()
        
        success = service.force_process_file(filename)
        
        if success:
            return {
                "message": f"Fichier {filename} traité avec succès",
                "filename": filename,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Échec du traitement de {filename}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

@router.post("/automation/scan")
async def scan_for_new_files():
    """Scanner manuellement les nouveaux fichiers"""
    try:
        from app.services.automation_service import get_automation_service
        service = get_automation_service()
        
        # Forcer un scan
        service._scan_and_process_new_files()
        
        return {
            "message": "Scan terminé",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du scan: {str(e)}") 