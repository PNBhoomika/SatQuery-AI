import React, { useState, useRef } from 'react';
import { Search, Image as ImageIcon, Upload, X, Loader2 } from 'lucide-react';
import { useIntelligence } from '../../context/IntelligenceContext';

export const SearchBar: React.FC = () => {
  const { activeQuery, setActiveQuery, executeSearch, executeImageSearch, isSearching } = useIntelligence();
  const [searchTab, setSearchTab] = useState<'text' | 'image'>('text');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const defaultExample = 'Find vegetation loss around Tumakuru between 2024 and 2026';

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const queryToRun = activeQuery.trim() || defaultExample;
    executeSearch(queryToRun);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleImageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      executeImageSearch(selectedFile);
    }
  };

  const removeImage = () => {
    setSelectedFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="w-full bg-[#070a10]/90 backdrop-blur-md border border-white/[0.08] rounded-xl p-3.5 shadow-xl">
      {/* Search Mode Header */}
      <div className="flex items-center justify-between gap-2 mb-2.5 pb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setSearchTab('text')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono tracking-wider uppercase transition-all ${
              searchTab === 'text'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-3 h-3" />
            <span>NATURAL LANGUAGE</span>
          </button>

          <button
            type="button"
            onClick={() => setSearchTab('image')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono tracking-wider uppercase transition-all ${
              searchTab === 'image'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ImageIcon className="w-3 h-3" />
            <span>IMAGE QUERY</span>
          </button>
        </div>

        <span className="hidden sm:inline-block text-[10px] font-mono text-slate-400 uppercase">
          VECTOR RETRIEVAL
        </span>
      </div>

      {/* Mode 1: Text Search */}
      {searchTab === 'text' && (
        <form onSubmit={handleTextSubmit} className="space-y-2.5">
          <div className="relative flex items-center">
            <input
              type="text"
              value={activeQuery}
              onChange={(e) => setActiveQuery(e.target.value)}
              placeholder={defaultExample}
              className="w-full bg-[#04060a] border border-white/15 focus:border-emerald-500/60 rounded-lg pl-3.5 pr-28 py-2.5 text-xs font-mono text-white placeholder-slate-400 transition-colors"
            />
            <div className="absolute right-1.5 flex items-center">
              <button
                type="submit"
                disabled={isSearching}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-mono text-[11px] font-bold uppercase tracking-wider transition-all"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin text-slate-950" />
                    <span>SEARCHING...</span>
                  </>
                ) : (
                  <span>SEARCH &rarr;</span>
                )}
              </button>
            </div>
          </div>

          {/* Quick Examples */}
          <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
            <span className="text-slate-400 uppercase">Try:</span>
            {[
              'Solar arrays in Tumakuru',
              'Flooded cropland near Krishna delta',
              'Canopy loss Western Ghats',
            ].map((eg) => (
              <button
                key={eg}
                type="button"
                onClick={() => {
                  setActiveQuery(eg);
                  executeSearch(eg);
                }}
                className="px-2 py-0.5 rounded border border-white/[0.06] bg-white/[0.02] text-slate-400 hover:text-slate-200 hover:border-white/20 transition-colors"
              >
                {eg}
              </button>
            ))}
          </div>
        </form>
      )}

      {/* Mode 2: Image Query */}
      {searchTab === 'image' && (
        <form onSubmit={handleImageSubmit} className="space-y-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*,.tif,.tiff"
            className="hidden"
          />

          {!imagePreview ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border border-dashed border-white/20 hover:border-emerald-500/50 rounded-lg p-5 text-center cursor-pointer bg-white/[0.01] hover:bg-white/[0.03] transition-all"
            >
              <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1.5" />
              <p className="text-xs font-mono text-slate-300">
                Click to drop target GeoTIFF or image tile
              </p>
              <p className="text-[10px] font-mono text-slate-400 mt-0.5">
                Extracts vision embeddings for visual similarity search
              </p>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-2 rounded-lg border border-white/10 bg-[#04060a]">
              <img
                src={imagePreview}
                alt="Query Tile"
                className="w-14 h-14 object-cover rounded border border-slate-700 shrink-0"
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-white truncate">{selectedFile?.name}</p>
                <p className="text-[10px] font-mono text-slate-400">
                  {selectedFile ? (selectedFile.size / 1024).toFixed(1) + ' KB' : ''}
                </p>
              </div>
              <button
                type="button"
                onClick={removeImage}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {selectedFile && (
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSearching}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold uppercase transition-all"
              >
                {isSearching ? 'EMBEDDING & RETRIEVING...' : 'SEARCH BY IMAGE →'}
              </button>
            </div>
          )}
        </form>
      )}
    </div>
  );
};
