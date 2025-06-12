import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { definePreset, palette } from '@primeng/themes';
import { NavigationItem } from '@triageflow/shared/models';
import { PrimeNG } from 'primeng/config';
import Aura from '@primeng/themes/aura';

@Component({
  imports: [RouterModule],
  selector: 'flow-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'block bg-surface-100',
  },
})
export class AppComponent {
  readonly #primeNgConfig = inject(PrimeNG);

  items: NavigationItem[] = [
    {
      label: 'Home',
      icon: 'home',
      route: '/',
    },
  ];

  constructor() {
    const triageFlowPrimaryPaletteLight = palette('#6069CE');
    const triageFlowPrimaryPaletteDark = palette('#858DE5');

    console.log(triageFlowPrimaryPaletteLight);

    const triageFlowPreset = definePreset(Aura, {
      semantic: {
        colorScheme: {
          light: {
            primary: {
              50: triageFlowPrimaryPaletteLight['50'],
              100: triageFlowPrimaryPaletteLight['100'],
              200: triageFlowPrimaryPaletteLight['200'],
              300: triageFlowPrimaryPaletteLight['300'],
              400: triageFlowPrimaryPaletteLight['400'],
              500: triageFlowPrimaryPaletteLight['500'],
              600: triageFlowPrimaryPaletteLight['600'],
              700: triageFlowPrimaryPaletteLight['700'],
              800: triageFlowPrimaryPaletteLight['800'],
              900: triageFlowPrimaryPaletteLight['900'],
              950: triageFlowPrimaryPaletteLight['950'],
            },
          },
          dark: {
            primary: {
              50: triageFlowPrimaryPaletteDark['50'],
              100: triageFlowPrimaryPaletteDark['100'],
              200: triageFlowPrimaryPaletteDark['200'],
              300: triageFlowPrimaryPaletteDark['300'],
              400: triageFlowPrimaryPaletteDark['400'],
              500: triageFlowPrimaryPaletteDark['500'],
              600: triageFlowPrimaryPaletteDark['600'],
              700: triageFlowPrimaryPaletteDark['700'],
              800: triageFlowPrimaryPaletteDark['800'],
              900: triageFlowPrimaryPaletteDark['900'],
              950: triageFlowPrimaryPaletteDark['950'],
            },
          },
        },
      },
    });

    this.#primeNgConfig.theme.set({
      preset: triageFlowPreset,
      options: {
        darkModeSelector: '.dark',
      },
    });
    this.#primeNgConfig.ripple.set(true);
  }
}
