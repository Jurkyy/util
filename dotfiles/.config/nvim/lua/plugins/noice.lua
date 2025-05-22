return {
  "folke/noice.nvim",
  opts = {
    lsp = {
      -- override markdown rendering so that **cmp** and other plugins use **Treesitter**
      override = {
        ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
        ["vim.lsp.util.stylize_markdown"] = true,
        ["cmp.entry.get_documentation"] = true,
      },
      progress = {
        enabled = false, -- Disable LSP progress messages
      },
    },
    commands = {
      nohlsearch = {
        enabled = false,
      },
    },
    messages = {
      enabled = false, -- Diagnostic: Disable messages UI
      view = "notify",
      view_error = "notify",
      view_warn = "notify",
      format = {
        default = { "{level} ", "{title} ", "{message}" },
        notify = { "{level} ", "{title} ", "{message}" },
      },
    },
    views = {
      notify = {
        format = { "{level} ", "{title} ", "{message}" },
      },
      mini = {
        format = { "{level} ", "{title} ", "{message}" },
      },
    },
    routes = {
      {
        filter = { event = "msg_show" },
        view = "notify",
        opts = {
          format = { "{level} ", "{title} ", "{message}" },
        },
      },
    },
    -- you can enable a preset configuration for lsp progress
    -- presets = {
    --   bottom_search = true, -- use a classic bottom cmdline for search
    --   command_palette = true, -- position the cmdline and popupmenu together
    --   long_message_to_split = true, -- long messages will be sent to a split
    --   inc_rename = false, -- don't show an input prompt for inc_rename
    --   lsp_doc_border = false, -- add a border to hover docs and signature help
    -- },
  },
} 