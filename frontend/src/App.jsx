import React, { useState } from 'react';
import { Search, TrendingUp, ShoppingCart, ExternalLink, Star, Filter, AlertCircle, Award, CheckCircle, Info } from 'lucide-react';

const API_URL = 'http://localhost:5000';

const PriceComparisonApp = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSource, setSelectedSource] = useState('all');
  const [sortBy, setSortBy] = useState('price-asc');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setProducts([]);

    try {
      const response = await fetch(`${API_URL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery })
      });

      const data = await response.json();

      if (data.success) {
        setProducts(data.products);
        if (data.products.length === 0) {
          setError('No products found. Try a different search term.');
        }
      } else {
        setError(data.error || 'Failed to fetch products');
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to connect to server. Make sure the backend is running on http://localhost:5000');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getSourceIcon = (source) => {
    const icons = {
      'Flipkart': '📱',
      'Amazon': '🛒',
      'Vijay Sales': '🏬',
      'JioMart': '🔵'
    };
    return icons[source] || '🛍️';
  };

  const filteredProducts = products
    .filter(p => selectedSource === 'all' || p.source === selectedSource)
    .filter(p => selectedCategory === 'all' || p.category === selectedCategory)
    .sort((a, b) => {
      if (sortBy === 'price-asc') return a.price_num - b.price_num;
      if (sortBy === 'price-desc') return b.price_num - a.price_num;
      return 0;
    });

  const categories = [...new Set(products.map(p => p.category))];
  const sources = [...new Set(products.map(p => p.source))];
  const bestDeal = filteredProducts.length > 0 ? filteredProducts[0] : null;

  return (
    
      {/* Header */}
      
        
          
            
              
              
                PriceWise
              
            
            
              
              Compare 4 platforms
            
          
          
          
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search for laptops, phones, headphones..."
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none transition-colors text-sm sm:text-base"
              disabled={loading}
            />
            
              
              {loading ? 'Searching...' : 'Search'}
            
          
        
      

      {/* Main Content */}
      
        {/* Error Banner */}
        {error && (
          
            
            {error}
          
        )}

        {/* Best Deal Banner */}
        {bestDeal && !loading && !error && (
          
            
              
              
                
                  Best Deal Found! 
                  
                
                
                  
                    {bestDeal.title}
                    
                      {bestDeal.price}
                      
                        {getSourceIcon(bestDeal.source)} {bestDeal.source}
                      
                    
                  
                  
                    View Deal 
                  
                
              
            
          
        )}

        {/* Filters */}
        {products.length > 0 && !loading && (
          
            
              
              Filters
            
            
              
                Source
                <select
                  value={selectedSource}
                  onChange={(e) => setSelectedSource(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-sm"
                >
                  All Sources ({products.length})
                  {sources.map(source => (
                    
                      {getSourceIcon(source)} {source} ({products.filter(p => p.source === source).length})
                    
                  ))}
                
              

              
                Category
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-sm"
                >
                  All Categories
                  {categories.map(cat => (
                    {cat}
                  ))}
                
              

              
                Sort By
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-sm"
                >
                  Price: Low to High
                  Price: High to Low
                
              
            
            
              Showing {filteredProducts.length} of {products.length} products
            
          
        )}

        {/* Loading State */}
        {loading && (
          
            
            Searching across platforms...
            This may take a few seconds
          
        )}

        {/* Products Grid */}
        {!loading && filteredProducts.length > 0 && (
          
            {filteredProducts.map((product, index) => (
              
                {product.image && (
                  
                    <img
                      src={product.image}
                      alt={product.title}
                      className="max-h-full max-w-full object-contain"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = '📦';
                      }}
                    />
                  
                )}
                
                
                  
                    
                      {getSourceIcon(product.source)} {product.source}
                    
                    {product.rating && (
                      
                        
                        {product.rating}
                      
                    )}
                  

                  
                    {product.title}
                  

                  {product.category && (
                    Category: {product.category}
                  )}

                  
                    
                      {product.price}
                      {product.original_price && product.original_price !== product.price && (
                        {product.original_price}
                      )}
                    
                    
                      View 
                    
                  
                
              
            ))}
          
        )}

        {/* Empty State */}
        {!loading && !error && products.length === 0 && (
          
            
            Start Your Search
            
              Enter a product name above to compare prices across Flipkart, Amazon, Vijay Sales, and JioMart
            
            
              
                
                
                  Popular searches:
                  iPhone 15, Samsung TV, Sony Headphones, MacBook Air, PlayStation 5
                
              
            
          
        )}
      

      {/* Footer */}
      
        
          PriceWise - Compare prices and find the best deals
          Searches across Flipkart, Amazon, Vijay Sales & JioMart
          Made with ❤️ for smart shoppers
        
      
    
  );
};
