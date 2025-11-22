"""Entity resolution service for natural language matching."""

import logging
from typing import List, Dict, Any, Callable, Optional
from rapidfuzz import fuzz, process

from .client import SplitwiseClient
from .models import ResolutionMatch

logger = logging.getLogger(__name__)


class EntityResolver:
    """Resolves natural language references to Splitwise entities.
    
    This service provides fuzzy matching capabilities to resolve user-provided
    text (like "John" or "roommates") to specific Splitwise entities such as
    friends, groups, and categories. It uses the rapidfuzz library for efficient
    fuzzy string matching.
    
    Attributes:
        client: SplitwiseClient instance for API access
        _friends_cache: Cached list of friends
        _groups_cache: Cached list of groups
    """
    
    def __init__(self, client: SplitwiseClient):
        """Initialize EntityResolver with SplitwiseClient instance.
        
        Args:
            client: SplitwiseClient instance for API access
        """
        self.client = client
        self._friends_cache: Optional[List[Dict[str, Any]]] = None
        self._groups_cache: Optional[List[Dict[str, Any]]] = None
        logger.info("EntityResolver initialized")
    
    def _fuzzy_match(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        key_func: Callable[[Dict[str, Any]], str],
        threshold: int = 70
    ) -> List[ResolutionMatch]:
        """Internal fuzzy matching logic using rapidfuzz.
        
        This method performs fuzzy string matching between a query and a list of
        candidates, returning matches that score above the specified threshold.
        
        Args:
            query: Search query string
            candidates: List of candidate dictionaries to match against
            key_func: Function to extract the string to match from each candidate
            threshold: Minimum match score (0-100) to include in results
            
        Returns:
            List of ResolutionMatch objects sorted by match score (highest first)
        """
        if not query or not candidates:
            logger.debug("Empty query or candidates list")
            return []
        
        # Extract strings to match against
        candidate_strings = []
        for candidate in candidates:
            try:
                string_value = key_func(candidate)
                if string_value:
                    candidate_strings.append((string_value, candidate))
            except (KeyError, TypeError) as e:
                logger.warning(f"Error extracting string from candidate: {e}")
                continue
        
        if not candidate_strings:
            logger.debug("No valid candidate strings extracted")
            return []
        
        # Perform fuzzy matching
        matches = []
        for candidate_str, candidate_data in candidate_strings:
            # Use token_sort_ratio for better matching with word order variations
            score = fuzz.token_sort_ratio(query.lower(), candidate_str.lower())
            
            if score >= threshold:
                matches.append((score, candidate_data))
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[0], reverse=True)
        
        # Convert to ResolutionMatch objects
        results = []
        for score, candidate_data in matches:
            # Extract ID and name based on entity type
            entity_id = candidate_data.get("id")
            entity_name = key_func(candidate_data)
            
            # Build additional info (exclude id and name to avoid duplication)
            additional_info = {
                k: v for k, v in candidate_data.items()
                if k not in ["id"] and v is not None
            }
            
            results.append(ResolutionMatch(
                id=entity_id,
                name=entity_name,
                match_score=float(score),
                additional_info=additional_info
            ))
        
        logger.debug(f"Fuzzy match for '{query}': found {len(results)} matches above threshold {threshold}")
        return results


    async def resolve_friend(self, query: str, threshold: int = 70) -> List[ResolutionMatch]:
        """Resolve friend name to user ID(s) using fuzzy matching.
        
        This method searches through the user's friends list and returns matches
        that score above the specified threshold. Results are cached to minimize
        API calls.
        
        Args:
            query: Natural language query (e.g., "John", "john smith")
            threshold: Minimum fuzzy match score (0-100, default: 70)
            
        Returns:
            List of ResolutionMatch objects with friend information, sorted by
            match score (highest first). Each match includes:
            - id: Friend's user ID
            - name: Friend's full name
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with email, balance, and other details
            
        Raises:
            Exception: If API request fails
        """
        logger.info(f"Resolving friend: '{query}' (threshold: {threshold})")
        
        # Fetch friends list if not cached
        if self._friends_cache is None:
            logger.debug("Fetching friends list from API")
            response = await self.client.get_friends()
            self._friends_cache = response.get("friends", [])
            logger.debug(f"Cached {len(self._friends_cache)} friends")
        
        # Define key function to extract full name from friend data
        def get_friend_name(friend: Dict[str, Any]) -> str:
            first_name = friend.get("first_name", "")
            last_name = friend.get("last_name", "")
            # Combine first and last name, handling cases where one might be missing
            full_name = f"{first_name} {last_name}".strip()
            return full_name if full_name else friend.get("email", "")
        
        # Perform fuzzy matching
        matches = self._fuzzy_match(
            query=query,
            candidates=self._friends_cache,
            key_func=get_friend_name,
            threshold=threshold
        )
        
        logger.info(f"Found {len(matches)} friend matches for '{query}'")
        return matches

    async def resolve_group(self, query: str, threshold: int = 70) -> List[ResolutionMatch]:
        """Resolve group name to group ID(s) using fuzzy matching.
        
        This method searches through the user's groups list and returns matches
        that score above the specified threshold. Results are cached to minimize
        API calls.
        
        Args:
            query: Natural language query (e.g., "roommates", "trip to paris")
            threshold: Minimum fuzzy match score (0-100, default: 70)
            
        Returns:
            List of ResolutionMatch objects with group information, sorted by
            match score (highest first). Each match includes:
            - id: Group ID
            - name: Group name
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with members, type, and other details
            
        Raises:
            Exception: If API request fails
        """
        logger.info(f"Resolving group: '{query}' (threshold: {threshold})")
        
        # Fetch groups list if not cached
        if self._groups_cache is None:
            logger.debug("Fetching groups list from API")
            response = await self.client.get_groups()
            self._groups_cache = response.get("groups", [])
            logger.debug(f"Cached {len(self._groups_cache)} groups")
        
        # Define key function to extract group name
        def get_group_name(group: Dict[str, Any]) -> str:
            return group.get("name", "")
        
        # Perform fuzzy matching
        matches = self._fuzzy_match(
            query=query,
            candidates=self._groups_cache,
            key_func=get_group_name,
            threshold=threshold
        )
        
        logger.info(f"Found {len(matches)} group matches for '{query}'")
        return matches

    async def resolve_category(self, query: str, threshold: int = 70) -> List[ResolutionMatch]:
        """Resolve category name to category ID(s) using fuzzy matching.
        
        This method searches through Splitwise categories and returns matches
        that score above the specified threshold. Categories are retrieved from
        the CacheManager which handles caching automatically.
        
        Args:
            query: Natural language query (e.g., "food", "groceries", "utilities")
            threshold: Minimum fuzzy match score (0-100, default: 70)
            
        Returns:
            List of ResolutionMatch objects with category information, sorted by
            match score (highest first). Each match includes:
            - id: Category ID
            - name: Category name
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with subcategories and other details
            
        Raises:
            Exception: If API request fails
        """
        logger.info(f"Resolving category: '{query}' (threshold: {threshold})")
        
        # Fetch categories from client (uses cache automatically)
        response = await self.client.get_categories()
        categories = response.get("categories", [])
        logger.debug(f"Retrieved {len(categories)} categories")
        
        # Flatten categories and subcategories for matching
        all_categories = []
        for category in categories:
            # Add main category
            all_categories.append(category)
            
            # Add subcategories if they exist
            subcategories = category.get("subcategories", [])
            for subcategory in subcategories:
                # Include parent category name in subcategory for better context
                subcategory_with_parent = subcategory.copy()
                parent_name = category.get("name", "")
                subcategory_name = subcategory.get("name", "")
                subcategory_with_parent["full_name"] = f"{parent_name} - {subcategory_name}"
                all_categories.append(subcategory_with_parent)
        
        logger.debug(f"Flattened to {len(all_categories)} total categories (including subcategories)")
        
        # Define key function to extract category name
        def get_category_name(category: Dict[str, Any]) -> str:
            # Use full_name for subcategories, otherwise use name
            return category.get("full_name", category.get("name", ""))
        
        # Perform fuzzy matching
        matches = self._fuzzy_match(
            query=query,
            candidates=all_categories,
            key_func=get_category_name,
            threshold=threshold
        )
        
        logger.info(f"Found {len(matches)} category matches for '{query}'")
        return matches
    
    def clear_cache(self) -> None:
        """Clear cached friends and groups data.
        
        This method should be called after operations that modify friends or groups
        to ensure fresh data is fetched on the next resolution request.
        """
        self._friends_cache = None
        self._groups_cache = None
        logger.info("EntityResolver cache cleared")
