from sentence_transformers import SentenceTransformer, util

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
        embeddings1 = self.model.encode(text1, convert_to_tensor=True)
        embeddings2 = self.model.encode(text2, convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        return float(cosine_scores[0][0])