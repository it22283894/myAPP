import torch
from torch_geometric.nn import SAGEConv

class FoodRiskGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(FoodRiskGNN, self).__init__()
        # GraphSAGE is used to capture multi-hop interactions (Proposal Section 3.1)
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        # Returns probabilistic risk scores (e.g., 0.75 likelihood)
        return torch.sigmoid(x)
