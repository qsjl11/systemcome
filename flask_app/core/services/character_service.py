from ..models import Character
from ..utils.constants import CULTIVATION_STAGES, DEFAULT_VALUES
from .. import db
from ..utils.logging_utils import get_logger

logger = get_logger()

class CharacterService:
    @staticmethod
    def get_or_create_character():
        """获取或创建角色"""
        character = Character.query.first()
        if not character:
            logger.info("创建新角色")
            character = Character()
            db.session.add(character)
            db.session.commit()
        return character

    @staticmethod
    def get_character_status():
        """获取角色状态"""
        character = CharacterService.get_or_create_character()
        logger.debug(f"获取角色状态 - 境界:{character.cultivation_stage}, 信任:{character.trust}, 压力:{character.stress}")
        current_stage = CULTIVATION_STAGES.get(character.cultivation_stage, "未知境界")
        
        return {
            # 基础五维
            'vitality': character.vitality,
            'spiritual_power': character.spiritual_power,
            'consciousness': character.consciousness,
            'physique': character.physique,
            'fortune': character.fortune,
            
            # 境界信息
            'cultivation_stage': current_stage,
            'cultivation_realm': character.cultivation_realm,
            'breakthrough_chance': character.breakthrough_chance,
            
            # 灵根资质
            'affinities': {
                'metal': character.metal_affinity,
                'wood': character.wood_affinity,
                'water': character.water_affinity,
                'fire': character.fire_affinity,
                'earth': character.earth_affinity
            },
            
            # 性格维度
            'personality': {
                'alignment': character.alignment,
                'decision_style': character.decision_style,
                'social_mode': character.social_mode,
                'fortune_sensitivity': character.fortune_sensitivity,
                'dao_heart': character.dao_heart
            },
            
            # 原有属性
            'trust': character.trust,
            'stress': character.stress
        }

    @staticmethod
    def update_character_attributes(updates):
        """更新角色属性"""
        character = CharacterService.get_or_create_character()
        
        logger.info(f"更新角色属性: {updates}")
        for attr, value in updates.items():
            if hasattr(character, attr):
                old_value = getattr(character, attr)
                setattr(character, attr, value)
                logger.debug(f"属性 {attr}: {old_value} -> {value}")
        
        db.session.commit()
        return character

    @staticmethod
    def apply_task_effects(task_type):
        """应用任务效果到角色属性"""
        from ..utils.constants import TASK_TYPES
        
        character = CharacterService.get_or_create_character()
        task_effects = TASK_TYPES.get(task_type, {})
        logger.info(f"应用任务效果 - 类型: {task_type}")
        
        if task_type == '战斗':
            vitality_gain = task_effects.get('vitality_gain', 0)
            stress_gain = task_effects.get('stress_gain', 0)
            character.vitality += vitality_gain
            character.stress += stress_gain
            logger.debug(f"战斗效果 - 体力增加: {vitality_gain}, 压力增加: {stress_gain}")
        elif task_type == '探索':
            sp_gain = task_effects.get('spiritual_power_gain', 0)
            cons_gain = task_effects.get('consciousness_gain', 0)
            character.spiritual_power += sp_gain
            character.consciousness += cons_gain
            logger.debug(f"探索效果 - 灵力增加: {sp_gain}, 意识增加: {cons_gain}")
        elif task_type == '社交':
            trust_gain = task_effects.get('trust_gain', 0)
            fortune_gain = task_effects.get('fortune_gain', 0)
            character.trust += trust_gain
            character.fortune += fortune_gain
            logger.debug(f"社交效果 - 信任增加: {trust_gain}, 机缘增加: {fortune_gain}")
        
        db.session.commit()
        return character

    @staticmethod
    def calculate_ai_action():
        """计算AI行动决策"""
        character = CharacterService.get_or_create_character()
        logger.info("开始计算AI行动决策")
        
        if character.stress > 70:
            action = '逃避' if character.decision_style < 50 else '莽撞行动'
            logger.debug(f"压力过高({character.stress}) - 选择{action}")
        elif character.spiritual_power < 150:
            action = '修炼'
            logger.debug(f"灵力不足({character.spiritual_power}) - 选择修炼")
        else:
            # 根据性格倾向调整探索概率
            explore_chance = 0.3 + (character.decision_style - 50) * 0.004
            action = '探索' if character.fortune_sensitivity > explore_chance * 100 else '社交'
            logger.debug(f"正常状态 - 选择{action} (探索概率: {explore_chance:.2%})")
        
        return {
            'action': action,
            'reason': f'当前状态: 灵力{character.spiritual_power}, 压力{character.stress}'
        }
