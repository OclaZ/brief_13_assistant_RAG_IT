import mlflow
# Assurez-vous que l'URL est correcte (localhost si lancé hors docker, mlflow si dans docker)
mlflow.set_tracking_uri("http://localhost:5000") 

client = mlflow.tracking.MlflowClient()
# On cherche l'expérience supprimée
experiments = client.search_experiments(view_type=mlflow.entities.ViewType.DELETED_ONLY)

for exp in experiments:
    if exp.name == "RAG_Default": # Mettez le nom qui bloque ici
        print(f"Restauration de l'expérience {exp.name} (ID: {exp.experiment_id})...")
        client.restore_experiment(exp.experiment_id)
        print("C'est fait !")