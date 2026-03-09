-- Read colors from the single source of truth: colors.toml
-- This prevents drift between terminals and Neovim
local function read_colors()
	local path = vim.fn.expand("~/.config/omarchy/current/theme/colors.toml")
	local file = io.open(path, "r")
	if not file then
		return nil
	end
	local ok, colors = pcall(function()
		local c = {}
		for line in file:lines() do
			local key, value = line:match('^(%w+)%s*=%s*"(#%x+)"')
			if key and value then
				c[key] = value
			end
		end
		return c
	end)
	file:close()
	if not ok then
		return nil
	end
	return colors
end

local c = read_colors()

-- Fallback: if colors.toml is missing or unreadable, use Kanso defaults
if not c then
	vim.notify("Crystal: colors.toml not found, using Kanso defaults", vim.log.levels.WARN)
	return {
		{ "webhooked/kanso.nvim", lazy = false, priority = 1000, opts = { background = { dark = "zen" } } },
		{ "LazyVim/LazyVim", opts = { colorscheme = "kanso-zen" } },
	}
end

return {
	{
		"webhooked/kanso.nvim",
		lazy = false,
		priority = 1000,
		opts = {
			background = { dark = "zen" },
			colors = {
				palette = {
					-- Map colors.toml → Kanso palette
					-- Foreground / background
					fg = c.foreground,
					fg2 = c.foreground,
					zenBg0 = c.background,
					zenBg1 = c.color0,
					zenBg2 = c.selection_background,
					-- ANSI reds
					red3 = c.color1,
					red2 = c.color9,
					-- ANSI greens
					green3 = c.color2,
					green2 = c.color10,
					green5 = c.color14,
					-- ANSI yellows
					yellow3 = c.color3,
					yellow2 = c.color11,
					-- ANSI blues
					blue3 = c.color4,
					blue = c.color12,
					blue2 = "#658594",
					-- Violet / pink
					pink = c.color5,
					violet = c.color13,
					violet2 = "#8992a7",
					-- Cyan / aqua
					aqua = c.color6,
					-- Orange (constants, string escapes)
					orange = "#b6927b",
					orange2 = "#b98d7b",
					-- Grays (operators, punctuation, comments, nontext)
					gray2 = c.color8,
					gray3 = "#909398",
					gray4 = "#75797f",
					gray5 = "#5C6066",
				},
			},
		},
	},
	{
		"LazyVim/LazyVim",
		opts = {
			colorscheme = "kanso-zen",
		},
	},
}
