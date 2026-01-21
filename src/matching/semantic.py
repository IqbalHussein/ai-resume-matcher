from sentence_transformers import SentenceTransformer, util
import torch

class SemanticMatcher:
    """
    A helper class to perform semantic similarity comparisons using Sentence Transformers.

    This class loads a pre-trained model to generate embeddings for text inputs
    and calculates cosine similarity between them. It is designed to capture
    contextual meaning beyond exact keyword matching.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the SemanticMatcher with a specific transformer model.

        Args:
            model_name: The HuggingFace model identifier to load.
                       Defaults to 'all-MiniLM-L6-v2' which offers a good
                       balance of speed and accuracy.
        """
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> torch.Tensor:
        """
        Generate embedding for a given text.
        
        Args:
            text: Input string.
            
        Returns:
            A pytorch tensor representing the text embedding.
        """
        if not text.strip():
            # Return a zero tensor of the correct size if text is empty to avoid errors
            # all-MiniLM-L6-v2 dimension is 384
            return torch.zeros(self.model.get_sentence_embedding_dimension())
        return self.model.encode(text, convert_to_tensor=True)

    def compute_similarity_score(self, embedding1: torch.Tensor, embedding2: torch.Tensor) -> float:
        """
        Compute cosine similarity between two pre-computed embeddings.
        
        Args:
            embedding1: First tensor.
            embedding2: Second tensor.
            
        Returns:
            Float similarity score [-1.0, 1.0].
        """
        cosine_scores = util.cos_sim(embedding1, embedding2)
        return float(cosine_scores[0][0])

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute the cosine similarity score between two text strings.

        Generates embeddings for both input texts and calculates the cosine
        similarity between their vectors.

        Args:
            text1: The first text string (e.g., resume content).
            text2: The second text string (e.g., job description).

        Returns:
            A float value between -1.0 and 1.0 representing the semantic similarity,
            where 1.0 indicates identical semantic meaning.
        """
        embeddings1 = self.encode(text1)
        embeddings2 = self.encode(text2)
        return self.compute_similarity_score(embeddings1, embeddings2)
