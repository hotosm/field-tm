const { EnvironmentPlugin } = require("webpack");
const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");

const deps = require("./package.json").dependencies;
module.exports = {
  output: {
    publicPath: `${process.env.FRONTEND_SCHEME}://${process.env.FRONTEND_DOMAIN}:${process.env.FMTM_OPENLAYER_MAP_PORT}/`,
  },

  resolve: {
    extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
  },

  devServer: {
    port: process.env.FMTM_OPENLAYER_MAP_PORT,
    historyApiFallback: true,
  },

  module: {
    rules: [
      {
        test: [/\.bmp$/, /\.gif$/, /\.jpe?g$/, /\.png$/, /\.ttf$/, /\.otf$/],
        loader: "file-loader",
        options: {
          name: "[name].[ext]",
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
      name: "fmtm_openlayer_map",
      filename: "remoteEntry.js",
      remotes: {
        fmtm: `fmtm@${process.env.FRONTEND_SCHEME}://${process.env.FRONTEND_DOMAIN}:${process.env.MAIN_PORT}/remoteEntry.js`,
      },
      exposes: {
        "./Map": "./src/App.jsx",
        "./Project": "./src/store/slices/ProjectSlice.js",
        "./ProjectDetails": "./src/views/Home.jsx",
        "./Persistor": "./src/store/store.js",
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
    new EnvironmentPlugin([
      "FRONTEND_SCHEME",
      "FRONTEND_DOMAIN",
      "MAIN_PORT",
      "FMTM_OPENLAYER_MAP_PORT",
    ]),
  ],
};
