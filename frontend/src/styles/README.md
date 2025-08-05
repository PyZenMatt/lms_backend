# 🎨 Styles Organization

Questa cartella contiene tutti gli stili del progetto organizzati per modularità e manutenibilità.

## 📁 Struttura

```
styles/
├── components/          # Stili per componenti riutilizzabili
│   ├── buttons.module.css
│   ├── cards.module.css
│   ├── forms.module.css
│   └── modals.module.css
├── views/              # Stili specifici per pagine/views
│   ├── dashboard.module.css
│   ├── courses.module.css
│   ├── profile.module.css
│   └── landing.module.css
├── layouts/            # Stili per layout e strutture
│   ├── admin-layout.module.css
│   ├── auth-layout.module.css
│   └── navigation.module.css
├── themes/             # Temi e variabili globali
│   ├── variables.css    # CSS Custom Properties
│   ├── skillshare-theme.css
│   └── responsive.css
└── global/             # Stili globali e reset
    ├── reset.css
    ├── typography.css
    └── utilities.css
```

## 🛠️ Convenzioni

### CSS Modules
- Usa `.module.css` per stili con scope locale
- Importa come: `import styles from './Component.module.css'`
- Classnames: `className={styles.componentName}`

### Naming Convention
- **Components**: `ComponentName.module.css`
- **Views**: `view-name.module.css` 
- **Themes**: `theme-name.css`
- **Utilities**: `utilities.css`

### Struttura File CSS
```css
/* 1. CSS Custom Properties */
:root {
  --primary-color: #007bff;
}

/* 2. Base styles */
.componentName {
  /* layout properties */
  /* visual properties */
  /* typography */
  /* interactions */
}

/* 3. Modifiers */
.componentName--variant { }

/* 4. States */
.componentName:hover { }
.componentName--active { }

/* 5. Responsive */
@media (max-width: 768px) { }
```

## 🎯 Obiettivi
- **Modularità**: Ogni componente ha i suoi stili
- **Riutilizzabilità**: Stili condivisi in utility classes  
- **Manutenibilità**: Struttura chiara e prevedibile
- **Performance**: CSS splitting per chunk ottimali
