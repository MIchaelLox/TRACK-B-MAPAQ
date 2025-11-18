"""
Module de Validation des Données - MAPAQ
=========================================
Validation et contrôle qualité des données du pipeline

Auteur: Grace MANDIANGU
Date: 2025-11-17
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Règle de validation"""
    field: str
    rule_type: str  # required, range, format, enum
    params: Dict[str, Any]
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Résultat de validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    record_id: str = None


class DataValidator:
    """Validateur de données pour le pipeline MAPAQ"""
    
    def __init__(self):
        self.rules = self._define_validation_rules()
    
    def _define_validation_rules(self) -> List[ValidationRule]:
        """Définit les règles de validation"""
        return [
            # Champs obligatoires
            ValidationRule('nom', 'required', {}, 'error'),
            ValidationRule('adresse', 'required', {}, 'error'),
            ValidationRule('score_risque', 'required', {}, 'error'),
            
            # Plages de valeurs
            ValidationRule('score_risque', 'range', {'min': 0, 'max': 100}, 'error'),
            ValidationRule('probabilite_infraction', 'range', {'min': 0, 'max': 1}, 'error'),
            ValidationRule('nb_infractions', 'range', {'min': 0, 'max': 100}, 'warning'),
            
            # Énumérations
            ValidationRule('categorie_risque', 'enum', 
                          {'values': ['critique', 'eleve', 'moyen', 'faible']}, 'error'),
            ValidationRule('taille', 'enum', 
                          {'values': ['petit', 'moyen', 'grand']}, 'warning'),
            
            # Formats
            ValidationRule('date_inspection', 'date_format', 
                          {'format': '%Y-%m-%d'}, 'error'),
            ValidationRule('prochaine_inspection', 'date_format', 
                          {'format': '%Y-%m-%d'}, 'warning'),
        ]
    
    def validate_record(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Valide un enregistrement selon les règles définies
        
        Args:
            record: Enregistrement à valider
        
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        
        for rule in self.rules:
            violation = self._check_rule(record, rule)
            
            if violation:
                if rule.severity == 'error':
                    errors.append(violation)
                else:
                    warnings.append(violation)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            record_id=record.get('id', 'unknown')
        )
    
    def validate_batch(self, records: List[Dict]) -> Tuple[List[Dict], List[ValidationResult]]:
        """
        Valide un lot d'enregistrements
        
        Args:
            records: Liste d'enregistrements
        
        Returns:
            Tuple (enregistrements valides, résultats de validation)
        """
        valid_records = []
        validation_results = []
        
        for record in records:
            result = self.validate_record(record)
            validation_results.append(result)
            
            if result.is_valid:
                valid_records.append(record)
            else:
                logger.warning(f"Enregistrement invalide {result.record_id}: {result.errors}")
        
        logger.info(f"Validation: {len(valid_records)}/{len(records)} valides")
        
        return valid_records, validation_results
    
    def _check_rule(self, record: Dict, rule: ValidationRule) -> str:
        """Vérifie une règle de validation"""
        field_value = record.get(rule.field)
        
        # Règle: champ obligatoire
        if rule.rule_type == 'required':
            if field_value is None or field_value == '':
                return f"Champ obligatoire manquant: {rule.field}"
        
        # Règle: plage de valeurs
        elif rule.rule_type == 'range':
            if field_value is not None:
                try:
                    value = float(field_value)
                    if value < rule.params['min'] or value > rule.params['max']:
                        return f"{rule.field} hors limites: {value} (attendu: {rule.params['min']}-{rule.params['max']})"
                except (ValueError, TypeError):
                    return f"{rule.field} n'est pas un nombre valide: {field_value}"
        
        # Règle: énumération
        elif rule.rule_type == 'enum':
            if field_value is not None and field_value not in rule.params['values']:
                return f"{rule.field} valeur invalide: {field_value} (attendu: {rule.params['values']})"
        
        # Règle: format de date
        elif rule.rule_type == 'date_format':
            if field_value:
                try:
                    datetime.strptime(field_value, rule.params['format'])
                except ValueError:
                    return f"{rule.field} format de date invalide: {field_value} (attendu: {rule.params['format']})"
        
        return None
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Génère un rapport de validation
        
        Args:
            results: Liste des résultats de validation
        
        Returns:
            Rapport de validation
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        all_errors = []
        all_warnings = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        report = {
            'total_records': total,
            'valid_records': valid,
            'invalid_records': invalid,
            'validation_rate': round(valid / total * 100, 2) if total > 0 else 0,
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'error_summary': self._summarize_issues(all_errors),
            'warning_summary': self._summarize_issues(all_warnings)
        }
        
        return report
    
    def _summarize_issues(self, issues: List[str]) -> Dict[str, int]:
        """Résume les problèmes par type"""
        summary = {}
        for issue in issues:
            # Extraire le type de problème (avant le ':')
            issue_type = issue.split(':')[0] if ':' in issue else issue
            summary[issue_type] = summary.get(issue_type, 0) + 1
        return summary


if __name__ == '__main__':
    # Test du validateur
    validator = DataValidator()
    
    test_records = [
        {
            'id': 'TEST_001',
            'nom': 'Restaurant Test',
            'adresse': '123 Rue Test',
            'score_risque': 75.5,
            'categorie_risque': 'eleve',
            'probabilite_infraction': 0.75,
            'date_inspection': '2024-11-01',
            'taille': 'moyen',
            'nb_infractions': 2
        },
        {
            'id': 'TEST_002',
            'nom': '',  # Erreur: nom manquant
            'adresse': '456 Rue Test',
            'score_risque': 150,  # Erreur: hors limites
            'categorie_risque': 'invalide',  # Erreur: valeur invalide
            'probabilite_infraction': 0.5,
            'date_inspection': '2024-11-01',
            'taille': 'moyen',
            'nb_infractions': 1
        }
    ]
    
    valid_records, results = validator.validate_batch(test_records)
    report = validator.generate_validation_report(results)
    
    print("\n" + "="*70)
    print("RAPPORT DE VALIDATION")
    print("="*70)
    print(f"Total: {report['total_records']}")
    print(f"Valides: {report['valid_records']}")
    print(f"Invalides: {report['invalid_records']}")
    print(f"Taux de validation: {report['validation_rate']}%")
    print(f"Erreurs: {report['total_errors']}")
    print(f"Avertissements: {report['total_warnings']}")
    print("="*70)
