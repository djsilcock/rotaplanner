module.exports = {
    "env": {
        "browser": true,
        "es2021": true
    },
    
    "overrides": [
    ],
    "parser": "@typescript-eslint/parser",
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "plugins": ["solid","@typescript-eslint"],
    "extends": ["eslint:recommended","plugin:@typescript-eslint/recommended", "plugin:solid/recommended"]
    ,
    "rules": {
    }
}
