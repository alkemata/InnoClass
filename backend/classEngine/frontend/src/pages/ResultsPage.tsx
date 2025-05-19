import { useLocation } from "react-router-dom";
import { useEffect, useState, useRef, useCallback } from "react";
import { api } from "../api";
import { Box, Typography, CircularProgress } from "@mui/material";
import ResultCard from "../components/ResultCard";

interface Hit {
  id: string;
  title: string;
  extracted_text: string;
  sdgs: string[];
  targets: string[];
  up: number;
  down: number;
}

export default function ResultsPage() {
  const { category, selections, keywords } = useLocation().state as any;
  const [hits, setHits] = useState<Hit[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const observer = useRef<IntersectionObserver>();

  const loadMore = useCallback(async () => {
    setLoading(true);
    const res = await api.post("/search", { category, selections, keywords, page, size: 20 });
    setHits(h => [...h, ...res.data.hits]);
    setLoading(false);
  }, [category, selections, keywords, page]);

  useEffect(() => { loadMore(); }, [loadMore]);

  const lastRef = useCallback((node: HTMLDivElement|null) => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) setPage(p => p+1);
    });
    if (node) observer.current.observe(node);
  }, [loading]);

  return (
    <Box p={4}>
      <Typography variant="h5">Results</Typography>
      {hits.map((h, i) => (
        <div key={h.id} ref={i === hits.length - 1 ? lastRef : null}>
          <ResultCard hit={h} category={category} />
        </div>
      ))}
      {loading && <CircularProgress sx={{ mt:2 }} />}
    </Box>
  );
}
