import { ThemeName, useTheme } from "../../store/theme-store";

const themes: ThemeName[] = ["light", "dark", "ocean", "graphite"];

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <label className="theme-switcher">
      <span className="theme-switcher__label">Theme</span>
      <select value={theme} onChange={(event) => setTheme(event.target.value as ThemeName)}>
        {themes.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
