const { EnvironmentPlugin } = require("webpack");
const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");

const deps = require("./package.json").dependencies;
module.exports = {
  output: {
    publicPath: `${process.env.FRONTEND_MAIN_URL}/`,
  },

  resolve: {
    extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
  },

  devServer: {
    host: "0.0.0.0",
    port: `${new URL(process.env.FRONTEND_MAIN_URL).port}`,
    historyApiFallback: true,
    allowedHosts: [`${process.env.FRONTEND_MAIN_URL}`],
  },
  devtool: "source-map",
  module: {
    rules: [
      {
        test: [/\.bmp$/, /\.gif$/, /\.jpe?g$/, /\.png$/, /\.ttf$/, /\.otf$/],
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 1000,
          },
        },
      },
      {
        test: /\.m?js/,
        type: "javascript/auto",
        resolve: {
          fullySpecified: false,
        },
      },
      {
        test: /\.(css|s[ac]ss)$/i,
        use: ["style-loader", "css-loader", "postcss-loader"],
      },
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
        },
      },
    ],
  },

  plugins: [
    new ModuleFederationPlugin({
      name: "fmtm",
      filename: "remoteEntry.js",
      remotes: {
        map: `fmtm_openlayer_map@${process.env.FRONTEND_MAP_URL}/remoteEntry.js`,
      },
      exposes: {
        "./ThemeSlice": "./src/store/slices/ThemeSlice.ts",
        "./HomeSlice": "./src/store/slices/HomeSlice.ts",
        "./BasicCard": "./src/utilities/BasicCard.tsx",
        "./BasicTabs": "./src/utilities/BasicTabs.tsx",
        "./CustomizedMenus": "./src/utilities/CustomizedMenus.tsx",
        "./CustomizedSnackbar": "./src/utilities/CustomizedSnackbar.jsx",
        "./PrimaryAppBar": "./src/utilities/PrimaryAppBar.tsx",
        "./environment": "./src/environment.ts",
        "./WindowDimension": "./src/hooks/WindowDimension.tsx",
        "./OnScroll": "./src/hooks/OnScroll.tsx",
        "./CoreModules": "./src/shared/CoreModules.js",
        "./AssetModules": "./src/shared/AssetModules.js"
      },
      shared: {
        ...deps,
        react: {
          singleton: true,
          requiredVersion: deps.react,
        },
        "react-dom": {
          singleton: true,
          requiredVersion: deps["react-dom"],
        },
      },
    }),
    new HtmlWebPackPlugin({
      template: "./src/index.html",
    }),
    new EnvironmentPlugin(["API_URL", "FRONTEND_MAIN_URL", "FRONTEND_MAP_URL"]),
  ],
};
