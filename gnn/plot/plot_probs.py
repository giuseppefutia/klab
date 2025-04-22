import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from kg-lab.eval.eval_funcs import predict_probabilities, predict_probabilities_batched

def compute_probabilities(models, data, metrics, mask_types=["test"]):
    """
    Computes and updates probabilities for licit and illicit classes across multiple GNN models.

    Args:
        models (dict): Dictionary of models where keys are model names and values are trained model instances.
        data (torch_geometric.data.Data): Graph data object containing node features and masks.
        metrics (dict): Dictionary to store computed probabilities.
        mask_types (list): List of mask types to compute probabilities for (e.g., ['train', 'test', 'val']).

    Example structure of metrics after updates:
    {
        'GCN': {
            'test': {
                'licit': {'probas': [...]},
                'illicit': {'probas': [...]}
            },
            'train': { ... }
        },
        'GAT': { ... },
        'GIN': { ... }
    }
    """
    for model_name, model in models.items():
        # Compute probabilities for each mask type
        for mask_type in mask_types:
            mask = getattr(data, f"{mask_type}_mask")  # Access the appropriate mask
            probas = predict_probabilities(model, data)[mask]

            # Split probabilities into licit (class 0) and illicit (class 1)
            probas_licit = probas[:, 0].cpu().numpy()
            probas_illicit = probas[:, 1].cpu().numpy()

            # Update the metrics dictionary
            if model_name not in metrics:
                metrics[model_name] = {}
            if mask_type not in metrics[model_name]:
                metrics[model_name][mask_type] = {}

            metrics[model_name][mask_type]['licit'] = {'probas': probas_licit}
            metrics[model_name][mask_type]['illicit'] = {'probas': probas_illicit}

def compute_probabilities_batched(models, dataloader, metrics, dataset_type, class_names, device='cpu'):
    """
    Computes and updates probabilities for specified classes across multiple GNN models with HeteroData.

    Args:
        models (dict): Dictionary of models where keys are model names and values are trained model instances.
        dataloader (torch.utils.data.DataLoader): DataLoader providing HeteroData batches.
        metrics (dict): Dictionary to store computed probabilities.
        dataset_type (str): Dataset type (e.g., 'train', 'val', 'test') used as the key in the metrics dictionary.
        class_names (list): List of class names (e.g., ['class_0', 'class_1']).
        device (str): Device to use for computation ('cpu' or 'cuda').

    Example structure of metrics after updates:
    {
        'GCN': {
            'train': {
                'class_0': {'probas': [...]},
                'class_1': {'probas': [...]}
            },
            'test': { ... }
        },
        'GAT': { ... },
        'GIN': { ... }
    }
    """
    if len(class_names) != 2:
        raise ValueError("This function supports binary classification, so `class_names` must have exactly two entries.")

    for model_name, model in models.items():
        model.to(device)

        # Use the provided function to compute probabilities for the specified edge type
        probas_class_1 = predict_probabilities_batched(
            model, dataloader, device=device
        ).cpu().numpy()

        # Probabilities for class_0 are 1 - class_1 probabilities
        probas_class_0 = 1 - probas_class_1

        # Update the metrics dictionary
        if model_name not in metrics:
            metrics[model_name] = {}
        if dataset_type not in metrics[model_name]:
            metrics[model_name][dataset_type] = {}

        # Populate the metrics for the specific dataset type
        metrics[model_name][dataset_type] = {
            class_names[0]: {'probas': probas_class_0},
            class_names[1]: {'probas': probas_class_1}
        }

def plot_predicted_probabilities(metrics, model_names, categories, title="Comparison of Predicted Probabilities Across GNN's"):
    """
    Creates a boxplot comparing predicted probabilities for specified categories across GNN models.

    Args:
        metrics (dict): Dictionary containing predicted probabilities per GNN model and class.
            Format: {model_name: {'test': {class_name: {'probas': [...]}}}}
        model_names (list): List of model names to include in the plot (e.g., ['gcn', 'gat', 'gin']).
        categories (list): List of category names to include in the plot (e.g., ['licit', 'illicit']).
        title (str): Title of the plot. Default is "Comparison of Predicted Probabilities Across GNN's".

    Example structure of metrics:
    {
        'GCN': {
            'test': {
                'licit': {'probas': [0.1, 0.2, 0.3]},
                'illicit': {'probas': [0.9, 0.8, 0.7]}
            }
        },
        'GAT': { ... },
        'GIN': { ... }
    }
    """
    # Prepare data for plotting
    data_temp = []
    for model in model_names:
        for category in categories:
            probas = metrics[model]['test'][category]['probas']
            data_temp.extend([(model.upper(), category.capitalize(), proba) for proba in probas])

    temp = pd.DataFrame(data_temp, columns=['Model', 'Class', 'Probability'])

    # Define plot properties
    plt.figure(figsize=(8, 4))
    flierprops = dict(marker='o', markerfacecolor='None', markersize=5, markeredgecolor='C0', alpha=0.2)

    # Create boxplot
    ax = sns.boxplot(
        y='Model',
        x='Probability',
        hue='Class',
        data=temp,
        linewidth=2.5,
        fliersize=0.5,
        palette={
            categories[0].capitalize(): "#0091ea",  # First category color
            categories[1].capitalize(): "#ffbd59"   # Second category color
        },
        flierprops=flierprops
    )

    # Customize plot appearance
    plt.grid(True, which='both', axis='x', color='lightgrey', linestyle='-', linewidth=0.5)
    plt.title(title)
    plt.xlabel("Predicted Probability")
    plt.ylabel("GNN Model")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), ncol=1)
    plt.tight_layout()
    plt.show()

