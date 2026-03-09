-- Delegate to active Omarchy theme
local path = vim.fn.expand("~/.config/omarchy/current/theme/neovim.lua")
if vim.fn.filereadable(path) == 1 then
	return dofile(path)
end
return {}
