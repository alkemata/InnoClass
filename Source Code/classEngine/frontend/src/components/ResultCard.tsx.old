import { Box, Typography, Chip, IconButton } from "@mui/material";
import ThumbUpOffAltIcon from "@mui/icons-material/ThumbUpOffAlt";
import ThumbDownOffAltIcon from "@mui/icons-material/ThumbDownOffAlt";
import { api } from "../api";

export default function ResultCard({
  hit,
  category
}: {
  hit: any;
  category: "sdg"|"target";
}) {
  const list = hit[category] as string[];

  const sendFeedback = async (type: "up"|"down") => {
    await api.post("/feedback", { doc_id: hit.id, feedback: type });
    // optionally update local state to reflect new count...
  };

  return (
    <Box
      sx={{
        border: "1px solid #ccc",
        borderRadius: 2,
        p:2,
        mt:2
      }}
    >
      <Typography variant="h6">{hit.title}</Typography>
      <Typography variant="body2" mt={1}>{hit.cleaned_text}</Typography>

      <Box mt={1}>
        {list.map(val => (
          <Chip key={val} label={val} sx={{ mr:1, mb:1 }} />
        ))}
      </Box>

      <Box mt={1}>
        <IconButton onClick={() => sendFeedback("up")}>
          <ThumbUpOffAltIcon />
        </IconButton>
        <IconButton onClick={() => sendFeedback("down")}>
          <ThumbDownOffAltIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
