import React from "react";
import PropTypes from "prop-types";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import CardPlaceholder from "components/CardPlaceholder";

const ACCENT_MAP = {
  info: {
    border: "rgba(0, 117, 255, 0.35)",
    glow: "rgba(0, 117, 255, 0.2)",
  },
  success: {
    border: "rgba(1, 181, 116, 0.4)",
    glow: "rgba(1, 181, 116, 0.2)",
  },
  warning: {
    border: "rgba(251, 207, 51, 0.35)",
    glow: "rgba(251, 207, 51, 0.25)",
  },
};

export function AchievementBadge({ label, value, description, accent = "info" }) {
  const palette = ACCENT_MAP[accent] || ACCENT_MAP.info;

  return (
    <VuiBox
      sx={{
        position: "relative",
        borderRadius: "16px",
        padding: "16px",
        border: `1px solid ${palette.border}`,
        background: "linear-gradient(135deg, rgba(8, 13, 48, 0.9), rgba(10, 14, 35, 0.65))",
        boxShadow: "0 10px 28px rgba(0, 0, 0, 0.25)",
        minHeight: "120px",
      }}
    >
      <VuiTypography variant="caption" color="text" fontWeight="medium">
        {label}
      </VuiTypography>
      <VuiTypography variant="h4" color="white" fontWeight="bold" mt={0.5}>
        {value}
      </VuiTypography>
      <VuiTypography variant="caption" color="text">
        {description}
      </VuiTypography>
    </VuiBox>
  );
}

AchievementBadge.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  description: PropTypes.string,
  accent: PropTypes.oneOf(["info", "success", "warning"]),
};

AchievementBadge.defaultProps = {
  description: "",
  accent: "info",
};

export function CardSpotlight({ card, formatDaysAgo, formatCurrency }) {
  if (!card) {
    return (
      <VuiBox
        sx={{
          borderRadius: "20px",
          border: "1px dashed rgba(255,255,255,0.2)",
          padding: "24px",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, rgba(11,17,56,0.95), rgba(20,28,75,0.85))",
          textAlign: "center",
        }}
      >
        <VuiTypography variant="caption" color="text">
          Spotlight Card
        </VuiTypography>
        <VuiTypography variant="h5" color="white" fontWeight="bold" mt={0.5}>
          Track a card to unlock highlights
        </VuiTypography>
        <VuiTypography variant="body2" color="text" mt={1}>
          Add preview images or mark a card for tracking to see it featured here.
        </VuiTypography>
      </VuiBox>
    );
  }

  const chips = [card.year, card.set_name, card.variety, card.parallel, card.card_number ? `#${card.card_number}` : null].filter(Boolean);
  const preview = card.preview_image_url || card.image_url || null;
  const lastChecked = card.last_price_check
    ? new Date(card.last_price_check).toLocaleString([], { month: "short", day: "numeric" })
    : card.days_ago !== undefined
    ? formatDaysAgo(card.days_ago)
    : "No recent activity";

  return (
    <VuiBox
      sx={{
        borderRadius: "20px",
        border: "1px solid rgba(0,117,255,0.25)",
        padding: "24px",
        height: "100%",
        background: "linear-gradient(135deg, rgba(11,17,56,0.95), rgba(20,28,75,0.85))",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <VuiTypography variant="caption" color="text" fontWeight="medium">
        Spotlight Card
      </VuiTypography>
      <VuiTypography variant="h4" color="white" fontWeight="bold">
        {card.player || "Untitled Card"}
      </VuiTypography>
      <VuiTypography variant="button" color="text">
        {card.team || "Unknown team"} {"\u2022"} {lastChecked}
      </VuiTypography>

      <VuiBox display="flex" gap={2} flexWrap="wrap">
        <VuiBox
          sx={{
            width: 120,
            height: 170,
            borderRadius: "14px",
            border: "1px solid rgba(255,255,255,0.1)",
            overflow: "hidden",
            background: "rgba(255,255,255,0.02)",
            flexShrink: 0,
          }}
        >
          {preview ? (
            <VuiBox component="img" src={preview} alt={card.player} sx={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <CardPlaceholder width={120} height={170} />
          )}
        </VuiBox>

        <VuiBox flex={1} minWidth={0}>
          <VuiTypography variant="button" color="text">
            Details
          </VuiTypography>
          <VuiBox display="flex" flexWrap="wrap" gap={1} mt={1}>
            {chips.map((chip) => (
              <VuiBox
                key={chip}
                px={1.5}
                py={0.5}
                sx={{
                  borderRadius: "999px",
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <VuiTypography variant="caption" color="white" fontWeight="medium">
                  {chip}
                </VuiTypography>
              </VuiBox>
            ))}
          </VuiBox>

          {typeof card.current_value === "number" && (
            <VuiBox mt={2}>
              <VuiTypography variant="caption" color="text">
                Estimated Value
              </VuiTypography>
              <VuiTypography variant="h4" color="success" fontWeight="bold">
                {formatCurrency(card.current_value)}
              </VuiTypography>
            </VuiBox>
          )}
        </VuiBox>
      </VuiBox>
    </VuiBox>
  );
}

CardSpotlight.propTypes = {
  card: PropTypes.object,
  formatDaysAgo: PropTypes.func,
  formatCurrency: PropTypes.func,
};

CardSpotlight.defaultProps = {
  card: null,
  formatDaysAgo: (days) => `${days}d ago`,
  formatCurrency: (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value || 0),
};

export function RecentAdditionItem({ item, formatDaysAgo }) {
  const title = `${item.player || "Unknown"} ${item.card_number ? `#${item.card_number}` : ""}`.trim();
  const meta = [item.year, item.set_name].filter(Boolean).join(" • ");

  return (
    <VuiBox display="flex" alignItems="center" gap={2} py={2}>
      {item.preview_image_url ? (
        <VuiBox
          component="img"
          src={item.preview_image_url}
          alt={title}
          sx={{
            width: 64,
            height: 90,
            borderRadius: "10px",
            objectFit: "cover",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        />
      ) : (
        <CardPlaceholder width={64} height={90} />
      )}
      <VuiBox flex={1}>
        <VuiTypography variant="button" color="white" fontWeight="bold">
          {title}
        </VuiTypography>
        <VuiTypography variant="caption" color="text">
          {meta || "No details"}
        </VuiTypography>
      </VuiBox>
      <VuiTypography variant="caption" color="text">
        {formatDaysAgo(item.days_ago || 0)}
      </VuiTypography>
    </VuiBox>
  );
}

RecentAdditionItem.propTypes = {
  item: PropTypes.shape({
    player: PropTypes.string,
    card_number: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    preview_image_url: PropTypes.string,
    year: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    set_name: PropTypes.string,
    days_ago: PropTypes.number,
  }).isRequired,
  formatDaysAgo: PropTypes.func,
};

RecentAdditionItem.defaultProps = {
  formatDaysAgo: (days) => `${days}d ago`,
};

export const formatDaysAgo = (days = 0) => {
  if (days <= 0) return "Today";
  if (days === 1) return "1 day ago";
  if (days < 7) return `${days} days ago`;
  const weeks = Math.floor(days / 7);
  return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
};

